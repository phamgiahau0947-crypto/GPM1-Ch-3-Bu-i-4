"""Phase 8 — Stress test (MT5): lịch sử, giả định và robustness.

Giai đoạn lấy từ config: GFC 2008, (2011–2012), 2018, COVID 2020, 2022.
Chỉ số "đánh giá thiếu rủi ro":
    UR_VaR = tỷ lệ vi phạm VaR99 thực tế / 1%;   UR_ES = mean(L_t / ES_t | L_t > VaR^{97,5}_t)
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from scipy import stats

from .backtest.var_tests import kupiec
from .config import enabled_periods, load_config, save_table

log = logging.getLogger(__name__)
MAIN = ["VN100", "VN50_SP50", "SP100"]


def max_drawdown(r: pd.Series) -> float:
    """Sụt giảm tối đa (dương) của giá trị tích lũy exp(Σ r)."""
    w = np.exp(r.cumsum())
    peak = np.maximum.accumulate(np.r_[1.0, w.values])[1:]
    return float(1 - (w.values / peak).min())


def reaction_lag(g: pd.DataFrame, tail_days: int = 60) -> float:
    """Số phiên từ lần vi phạm VaR99 đầu tiên trong giai đoạn (cú sốc) đến khi VaR99 ≥ 2× mức tại cú sốc."""
    hits = np.flatnonzero(g["exc_99"].values)
    if hits.size == 0:
        return np.nan
    k = hits[0]
    base = g["VaR_99"].iloc[k]
    after = np.flatnonzero(g["VaR_99"].values[k:k + tail_days] >= 2 * base)
    return float(after[0]) if after.size else np.nan


def historical_stress(fc: pd.DataFrame, returns: pd.DataFrame, corr: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """T11: chỉ số theo giai đoạn × danh mục × mô hình."""
    rows = []
    full_corr = returns["VN"].corr(returns["SP_VND"])
    for key, p in enabled_periods(cfg).items():
        sub_r = returns.loc[p["start"]:p["end"]]
        c_in = sub_r["VN"].corr(sub_r["SP_VND"])
        c_roll = corr.loc[p["start"]:p["end"], "corr_63"].mean()
        for (port, model), g in fc[fc["portfolio"].isin(MAIN)].groupby(["portfolio", "model"]):
            g = g.set_index("Date").loc[p["start"]:p["end"]]
            if len(g) < 10:
                continue
            loss = -g["realized"]
            hit975 = loss > g["VaR_975"]
            k = kupiec(g["exc_99"].values, 0.01)
            rows.append({
                "period": key, "label": p["label"], "portfolio": port, "model": model, "N": len(g),
                "mean_VaR99": g["VaR_99"].mean(), "mean_ES975": g["ES_975"].mean(), "worst_loss": loss.max(),
                "max_drawdown": max_drawdown(sub_r[port]) if port in sub_r else np.nan,
                "exc99": int(g["exc_99"].sum()), "rate99": g["exc_99"].mean(), "p_kupiec99": k["p_uc"],
                "exc975": int(hit975.sum()), "UR_VaR99": g["exc_99"].mean() / 0.01,
                "UR_ES": float((loss[hit975] / g["ES_975"][hit975]).mean()) if hit975.any() else np.nan,
                "corr_period": c_in, "corr63_mean": c_roll, "corr_full": full_corr,
                "reaction_lag_days": reaction_lag(g),
            })
    return pd.DataFrame(rows)


def worst_models(t11: pd.DataFrame) -> pd.DataFrame:
    """T11b: mô hình đánh giá thiếu rủi ro nhất (UR_VaR99 cao nhất, rồi UR_ES) theo giai đoạn × danh mục."""
    d = t11.dropna(subset=["UR_VaR99"]).sort_values(["UR_VaR99", "UR_ES"], ascending=False)
    worst = d.groupby(["period", "portfolio"]).head(1).assign(role="đánh giá thiếu nhất")
    best = d.assign(gap=(d["UR_VaR99"] - 1).abs()).sort_values("gap").groupby(["period", "portfolio"]).head(1)
    return pd.concat([worst, best.assign(role="sát kỳ vọng nhất").drop(columns="gap")]).sort_values(["period", "portfolio", "role"])


def normal_var_es(w: np.ndarray, vols: np.ndarray, rho: float, mu: np.ndarray | None = None) -> tuple[float, float]:
    """VaR99/ES97,5 Normal của danh mục 2 tài sản với tương quan ρ."""
    cov = np.array([[vols[0] ** 2, rho * vols[0] * vols[1]], [rho * vols[0] * vols[1], vols[1] ** 2]])
    s = float(np.sqrt(w @ cov @ w))
    m = float(w @ mu) if mu is not None else 0.0
    return -(m + s * stats.norm.ppf(0.01)), -m + s * stats.norm.pdf(stats.norm.ppf(0.975)) / 0.025


def hypothetical(returns: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """T12: kịch bản giả định trên danh mục 1 tỷ VND (tái định giá đầy đủ, lợi suất đơn)."""
    h = cfg["hypothetical"]
    V = h["notional_vnd"]
    rows = []
    scen = {"VND mất giá 5% (USD/VND +5%)": (0.0, 0.0, h["fx_shock"]),
            "VN −7% (sàn HOSE) & S&P −10%": (h["vn_shock"], h["sp_shock"], 0.0),
            "VN −7%, S&P −10% & VND mất giá 5%": (h["vn_shock"], h["sp_shock"], h["fx_shock"])}
    for port, (wv, ws) in cfg["portfolios"]["grid"].items():
        for name, (dv, ds, dfx) in scen.items():
            pnl = wv * dv + ws * ((1 + ds) * (1 + dfx) - 1)
            rows.append({"scenario": name, "portfolio": port, "pnl_pct": pnl, "pnl_vnd": pnl * V})
    gfc = cfg["stress_periods"]["GFC_2008"]
    for lab, d in (("toàn kỳ", returns), ("biến động GFC 2008", returns.loc[gfc["start"]:gfc["end"]])):
        vols = d[["VN", "SP_VND"]].std().values
        rho0 = d["VN"].corr(d["SP_VND"])
        for port, (wv, ws) in cfg["portfolios"]["grid"].items():
            w = np.array([wv, ws])
            v0, e0 = normal_var_es(w, vols, rho0)
            v1, e1 = normal_var_es(w, vols, h["stressed_corr"])
            rows.append({"scenario": f"Tương quan {rho0:.2f} → {h['stressed_corr']} (σ {lab})", "portfolio": port,
                         "VaR99_base": v0, "VaR99_stressed": v1, "ES975_base": e0, "ES975_stressed": e1,
                         "pnl_pct": -e1, "pnl_vnd": -e1 * V, "dES_pct": 100 * (e1 / e0 - 1)})
    return pd.DataFrame(rows)


def robustness(t5: pd.DataFrame) -> pd.DataFrame:
    """T13: tỷ lệ vi phạm và hai p-value VaR dưới các cấu hình robustness."""
    out = t5[t5["level"] == 0.99][
        ["set", "portfolio", "model", "window", "refit", "T", "x", "rate", "p_uc", "p_ind", "p_cc"]
    ].copy()
    out["config"] = out["set"] + " | W=" + out["window"].astype(str) + " | k=" + out["refit"].astype(str)
    return out.sort_values(["portfolio", "config", "model"])


def mt5_text(t11: pd.DataFrame, wm: pd.DataFrame) -> str:
    core = t11[t11["period"].isin(load_config()["core_stress"])]
    agg = core.groupby("model")["UR_VaR99"].mean().sort_values(ascending=False)
    w = wm[wm["role"] == "đánh giá thiếu nhất"]
    freq = w["model"].value_counts()
    cond = {"GARCH_N"}
    lag = core.assign(cls=np.where(core["model"].isin(cond), "có điều kiện", "phi điều kiện"))
    lag = lag.groupby("cls")["reaction_lag_days"].median()
    short = sorted(set(core["model"]) - set(core[core["period"] == "GFC_2008"]["model"]))
    top3 = ", ".join(f"{k} ({v})" for k, v in freq.head(3).items())
    note = (f" Lưu ý: {', '.join(short)} chưa có cửa sổ dự báo đủ tại GFC 2008; trung bình chỉ gồm các giai đoạn có dự báo."
            if short else "")
    return (f"- Trung bình qua {core['period'].nunique()} giai đoạn lõi và 3 danh mục, tỷ lệ vi phạm VaR99 gấp {agg.iloc[0]:.1f} lần "
            f"kỳ vọng với {agg.index[0]} (cao nhất) và {agg.iloc[-1]:.1f} lần với {agg.index[-1]} (thấp nhất) — T11_stress_historical.{note}\n"
            f"- Mô hình xuất hiện nhiều nhất ở vị trí 'đánh giá thiếu rủi ro nhất': {top3} — T11b_stress_worst_models.\n"
            f"- Số phiên trung vị từ vi phạm VaR99 đầu tiên trong giai đoạn đến khi VaR99 tăng gấp đôi: mô hình có điều kiện "
            f"{lag.get('có điều kiện', np.nan):.0f} phiên, mô hình phi điều kiện {lag.get('phi điều kiện', np.nan):.0f} phiên "
            "(cột reaction_lag_days; bỏ qua trường hợp VaR không tăng gấp đôi trong 60 phiên).")


def run(cfg: dict | None = None) -> str:
    from .config import path_of, read_table
    from .portfolio import load_returns
    from .rolling import load_forecasts

    cfg = cfg or load_config()
    returns = load_returns(cfg)
    corr = pd.read_parquet(path_of("processed", cfg) / "correlations.parquet")
    fc = load_forecasts(cfg, "main")
    t11 = historical_stress(fc, returns, corr, cfg)
    wm = worst_models(t11)
    save_table(t11, "T11_stress_historical")
    save_table(wm, "T11b_stress_worst_models")
    save_table(hypothetical(returns, cfg), "T12_stress_hypothetical")
    t5 = read_table("T5_backtest_var")
    save_table(robustness(t5), "T13_robustness")
    return mt5_text(t11, wm)
