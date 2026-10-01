"""Backtest VaR bằng Kupiec và Christoffersen."""

from __future__ import annotations

import logging

import pandas as pd

from ..config import load_config, save_table
from ..models import MODEL_LABELS
from .var_tests import christoffersen

log = logging.getLogger(__name__)
LEVELS = {"95": 0.95, "975": 0.975, "99": 0.99}


def var_conclusion(row: dict, alpha: float) -> str:
    """Kết luận dựa duy nhất trên p-value Kupiec và Christoffersen."""
    failures = []
    if row["p_uc"] < alpha:
        failures.append("Kupiec bác bỏ tần suất vi phạm")
    if row["p_cc"] < alpha:
        failures.append("Christoffersen bác bỏ bao phủ có điều kiện")
    return "Đạt: không bác bỏ Kupiec và Christoffersen" if not failures else "Không đạt: " + "; ".join(failures)


def backtest_var(g: pd.DataFrame, alpha: float = 0.05) -> list[dict]:
    """Backtest VaR 95/97,5/99 cho một danh mục, mô hình, cửa sổ và cấu hình."""
    rows = []
    for lab, q in LEVELS.items():
        hits = g[f"exc_{lab}"].values
        res = {"level": q, "p": 1 - q, **christoffersen(hits, 1 - q)}
        res["conclusion"] = var_conclusion(res, alpha)
        rows.append(res)
    return rows


def run(fc_all: pd.DataFrame | None = None, cfg: dict | None = None) -> dict[str, pd.DataFrame]:
    """Chạy hai kiểm định VaR cho mọi cấu hình forecast và lưu T5."""
    from ..rolling import load_forecasts

    cfg = cfg or load_config()
    fc_all = fc_all if fc_all is not None else load_forecasts(cfg, None)
    keys = ["portfolio", "model", "window", "set", "refit"]
    rows = []
    for key, group in fc_all.groupby(keys):
        group = group.sort_values("Date")
        for result in backtest_var(group, cfg["backtest"]["alpha_test"]):
            rows.append(dict(zip(keys, key)) | {
                "start": group["Date"].min().date(),
                "end": group["Date"].max().date(),
            } | result)
    table = pd.DataFrame(rows)
    table["label"] = table["model"].map(MODEL_LABELS)
    save_table(table, "T5_backtest_var")
    log.info("Kupiec/Christoffersen xong: %d dòng", len(table))
    return {"T5": table}


def pass_table(t5: pd.DataFrame, alpha: float = 0.05) -> pd.DataFrame:
    """Tổng hợp mô hình không bị bác bỏ bởi cả hai kiểm định ở VaR 99%."""
    result = t5[(t5["set"] == "main") & (t5["level"] == 0.99)].copy()
    result["pass_kupiec"] = result["p_uc"] >= alpha
    result["pass_christoffersen"] = result["p_cc"] >= alpha
    result["pass_all"] = result["pass_kupiec"] & result["pass_christoffersen"]
    return result
