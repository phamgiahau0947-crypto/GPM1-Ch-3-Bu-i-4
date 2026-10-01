"""Phase 4 — Engine dự báo cuốn chiếu (rolling) VaR/ES 1 ngày.

Nguyên tắc chống look-ahead: tại ngày t dùng cửa sổ r[t−W+1 .. t] (W quan sát, **kết thúc
tại t**) để dự báo cho t+1; dự báo được lưu **cùng dòng với r[t+1]** (lợi suất thực tế).

    I_{t+1}(q) = 1  nếu  r_{t+1} < −VaR_{t}(q)

Mô hình họ GARCH được ước lượng lại mỗi k ngày (config); giữa các lần ước lượng, σ được
cập nhật bằng đệ quy với tham số cũ trên cửa sổ hiện tại. Nếu ước lượng không hội tụ (hoặc
không dừng) thì dùng tham số lần trước và đếm số lần.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from joblib import Parallel, delayed

from .config import load_config, path_of
from .models import MODELS
from .models.garch import fit_garch, garch_forecast_from_fit

log = logging.getLogger(__name__)

COLS = ["VaR_95", "VaR_975", "VaR_99", "ES_975", "sigma"]


@dataclass
class Task:
    """Một tổ hợp (danh mục × mô hình × cửa sổ × tần suất refit) cần chạy rolling."""

    portfolio: str
    model: str
    window: int
    refit: int
    set: str = "main"
    dates: tuple[str, str] | None = None     # giới hạn ngày dự báo (robustness refit)
    series: np.ndarray = field(default=None, repr=False)
    index: pd.DatetimeIndex = field(default=None, repr=False)


class _Refitter:
    """Quản lý tham số GARCH(1,1) được ước lượng lại định kỳ."""

    def __init__(self, model: str, refit: int, cfg: dict):
        self.model, self.refit, self.cfg = model, refit, cfg
        self.param, self.count, self.failures, self.fits = None, 0, 0, 0

    def update(self, window: np.ndarray) -> None:
        if self.param is not None and self.count % self.refit != 0:
            self.count += 1
            return
        self.count += 1
        self.fits += 1
        try:
            fit, _ = fit_garch(window, start=self.param)
            ok = fit.converged
        except Exception:  # noqa: BLE001 — lỗi tối ưu hóa hiếm gặp: dùng tham số cũ
            fit, ok = None, False
        if ok or self.param is None:
            self.param = fit if fit is not None else self.param
            self.failures += int(not ok)
        else:
            self.failures += 1


def _forecast_one(model: str, window: np.ndarray, state: _Refitter | None, cfg: dict) -> dict:
    rk = cfg["risk"]
    lv, es = tuple(rk["var_levels"]), rk["es_level"]
    if model == "GARCH_N":
        return garch_forecast_from_fit(window, state.param, lv, es)
    kw = {"n_paths": rk["mc_paths"], "seed": cfg["seed"]}
    return MODELS[model](window, lv, es, **kw)


def rolling_forecast(r: np.ndarray, model: str, window: int, refit: int = 20, cfg: dict | None = None,
                     t_mask: np.ndarray | None = None) -> tuple[np.ndarray, dict]:
    """Chạy rolling cho một chuỗi. Dòng t+1 của kết quả là dự báo lập tại t (NaN nếu chưa đủ cửa sổ).

    ``t_mask[t+1] = False`` → bỏ qua ngày dự báo đó (dùng cho mẫu con).
    """
    cfg = cfg or load_config()
    n = len(r)
    out = np.full((n, len(COLS)), np.nan)
    needs_state = model == "GARCH_N"
    state = _Refitter(model, refit, cfg) if needs_state else None
    for t in range(window - 1, n - 1):
        if t_mask is not None and not t_mask[t + 1]:
            continue
        w = r[t - window + 1: t + 1]
        if state is not None:
            state.update(w)
        f = _forecast_one(model, w, state, cfg)
        out[t + 1] = [f["VaR_95"], f["VaR_975"], f["VaR_99"], f["ES_975"], f["params"].get("sigma", np.nan)]
    meta = {"fits": state.fits if state else 0, "failures": state.failures if state else 0}
    return out, meta


def _task_key(task: Task, cfg: dict) -> str:
    h = hashlib.md5(np.ascontiguousarray(task.series).tobytes())
    h.update(repr((task.model, task.window, task.refit, task.dates, cfg["risk"], cfg["seed"])).encode())
    return f"{task.set}__{task.portfolio}__{task.model}__W{task.window}__k{task.refit}__{h.hexdigest()[:10]}"


def run_task(task: Task, cfg: dict) -> tuple[pd.DataFrame, dict]:
    """Chạy một Task (có cache parquet)."""
    cache = path_of("processed", cfg) / "rolling_cache"
    cache.mkdir(exist_ok=True)
    f = cache / f"{_task_key(task, cfg)}.parquet"
    fm = f.with_suffix(".json")
    if f.exists():
        meta = json.loads(fm.read_text()) if fm.exists() else {}
        return pd.read_parquet(f), meta | {"cached": True}
    t0 = time.perf_counter()
    mask = None
    if task.dates:
        mask = np.asarray((task.index >= task.dates[0]) & (task.index <= task.dates[1]))
    arr, meta = rolling_forecast(task.series, task.model, task.window, task.refit, cfg, mask)
    df = pd.DataFrame(arr, columns=COLS, index=task.index)
    df["realized"] = task.series
    df = df.dropna(subset=["VaR_99"])
    for c, q in (("exc_95", "VaR_95"), ("exc_975", "VaR_975"), ("exc_99", "VaR_99")):
        df[c] = (df["realized"] < -df[q]).astype(int)
    df = df.assign(portfolio=task.portfolio, model=task.model, window=task.window, refit=task.refit,
                   set=task.set).reset_index()
    meta.update(seconds=time.perf_counter() - t0, cached=False)
    df.to_parquet(f)
    fm.write_text(json.dumps(meta))
    return df, meta


def build_tasks(returns: pd.DataFrame, returns_lag: pd.DataFrame, cfg: dict) -> list[Task]:
    """Danh sách mọi tổ hợp cần chạy (Phase 4 + robustness Phase 8 + MT3)."""
    rk = cfg["risk"]
    tasks: list[Task] = []

    def add(df, port, model, window, refit=rk["garch_refit_every"], set_="main", dates=None):
        tasks.append(Task(port, model, window, refit, set_, dates, df[port].values, df.index))

    for port in cfg["portfolios"]["main"]:
        for m in cfg["models_main"]:
            add(returns, port, m, rk["window"])
    for port in ("W75_25", "W25_75"):
        for m in cfg["models_main"]:
            add(returns, port, m, rk["window"], set_="grid")
    for port in ("SP_USD", "VN50_SP50_USD"):                          # MT3: không quy đổi VND
        for m in cfg["models_main"]:
            add(returns, port, m, rk["window"], set_="usd")
    for port in cfg["portfolios"]["main"]:
        for m in cfg["models_main"]:
            for w in rk["robust_windows"]:
                add(returns, port, m, w, set_="robust_window")
        for k in rk["robust_refit"]:
            if k != rk["garch_refit_every"]:
                add(returns, port, "GARCH_N", rk["window"], k, "robust_refit", tuple(rk["robust_refit_sample"]))
        for m in cfg["models_main"]:
            add(returns_lag, port, m, rk["window"], set_="lagged")
    return tasks


def run(cfg: dict | None = None) -> pd.DataFrame:
    """Chạy song song mọi Task (joblib), ghép và lưu ``rolling_forecasts.parquet``."""
    from .portfolio import load_returns

    cfg = cfg or load_config()
    tasks = build_tasks(load_returns(cfg), load_returns(cfg, lagged=True), cfg)
    log.info("Rolling: %d tổ hợp, n_jobs = %s", len(tasks), cfg["risk"]["n_jobs"])
    res = Parallel(n_jobs=cfg["risk"]["n_jobs"], verbose=0)(delayed(run_task)(t, cfg) for t in tasks)
    frames, metas = [], []
    for t, (df, meta) in zip(tasks, res):
        frames.append(df)
        metas.append({"set": t.set, "portfolio": t.portfolio, "model": t.model, "window": t.window,
                      "refit": t.refit, "n_forecasts": len(df), **meta})
    out = pd.concat(frames, ignore_index=True)
    out.to_parquet(path_of("processed", cfg) / "rolling_forecasts.parquet")
    meta = pd.DataFrame(metas)
    from .config import save_table

    save_table(meta, "T4b_rolling_runtime")
    main = out[out["set"] == "main"]
    nan_share = main[COLS[:4]].isna().mean().max()
    log.info("Rolling xong: %d dòng; tỷ lệ NaN (main) = %.3f%%", len(out), 100 * nan_share)
    return out


def load_forecasts(cfg: dict | None = None, set_: str | None = "main") -> pd.DataFrame:
    """Đọc lại kết quả rolling (lọc theo ``set`` nếu chỉ định)."""
    df = pd.read_parquet(path_of("processed", cfg) / "rolling_forecasts.parquet")
    return df if set_ is None else df[df["set"] == set_].copy()
