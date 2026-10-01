"""Phase 1.4 — Lạm phát từ CPI và chia bối cảnh lạm phát (MT3).

Nguồn: CPI Việt Nam từ IMF International Financial Statistics (IFS), tần suất tháng, chỉ số gốc 2010 = 100.
Lạm phát so cùng kỳ: π_t = CPI_t / CPI_{t−12} − 1. File clean có sẵn cột ``Inflation_YoY`` (%); khi nạp, code
kiểm tra cột này khớp công thức trên (lệch > 1e−6 điểm % thì báo lỗi). Kiểm chứng: 12/2008 = 19,89% — khớp số
công bố. CPI **chỉ** dùng để tính lạm phát và chia bối cảnh, không đi vào VaR hằng ngày (CLAUDE.md §2).
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from .config import ROOT, load_config, path_of

log = logging.getLogger(__name__)


def classify_regimes(infl: pd.Series, threshold: float) -> pd.DataFrame:
    """Chia chế độ lạm phát: chính (ngưỡng cố định), robustness (trung vị, tam phân vị)."""
    x = infl.dropna()
    med = x.median()
    t1, t2 = x.quantile([1 / 3, 2 / 3])
    return pd.DataFrame({
        "regime": np.where(infl > threshold, "Cao", "Thấp"),
        "regime_median": np.where(infl > med, "Cao", "Thấp"),
        "regime_tercile": pd.cut(infl, [-np.inf, t1, t2, np.inf], labels=["Thấp", "Trung bình", "Cao"]).astype(str),
    }, index=infl.index).where(infl.notna())


def map_to_daily(monthly: pd.DataFrame, dates: pd.DatetimeIndex, lag_months: int = 0) -> pd.DataFrame:
    """Gán giá trị tháng cho từng ngày giao dịch.

    ``lag_months = 0``: ngày trong tháng m nhận giá trị tháng m (dùng để **diễn giải**).
    ``lag_months = 1``: nhận giá trị tháng m−1 — phiên bản "đã công bố", tránh look-ahead.
    """
    period = dates.to_period("M") - lag_months
    m = monthly.copy()
    m.index = m.index.to_period("M")
    out = m.reindex(period)
    out.index = dates
    return out


def load_cpi_cleaned(cfg: dict | None = None) -> pd.DataFrame:
    """Nạp trực tiếp CPI và Lạm phát YoY từ file clean duy nhất được cấu hình."""
    cfg = cfg or load_config()
    cleaned_dir = ROOT / cfg["cleaned_files"]["directory"]
    filename = cfg["cleaned_files"]["cpi"]
    p = cleaned_dir / filename
    if not p.exists():
        raise FileNotFoundError(f"Không tìm thấy file CPI clean: {p}")
    log.info("Đang đọc CPI clean từ %s...", p)
    df = pd.read_csv(p)
    required = {"Date", "CPI", "Inflation_YoY"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{p}: thiếu cột bắt buộc {', '.join(sorted(missing))}")
    dates = pd.to_datetime(df["Date"], errors="coerce")
    if dates.isna().any():
        raise ValueError(f"{p}: ngày không hợp lệ trong file CPI clean")
    if not dates.is_monotonic_increasing or dates.duplicated().any():
        raise ValueError(f"{p}: ngày phải tăng dần và không trùng")
    if df.empty:
        raise ValueError(f"{p}: file không có dữ liệu")
    df["Date"] = dates
    df = df.set_index("Date")
    # Inflation_YoY trong file của nhóm tính theo % (vd. 8.815 -> 0.08815)
    infl_yoy = df["Inflation_YoY"].astype(float) / 100.0
    cpi_idx = df["CPI"].astype(float)
    if cpi_idx.isna().any() or not np.isfinite(cpi_idx).all() or not (cpi_idx > 0).all():
        raise ValueError(f"{p}: CPI phải là số hữu hạn dương")
    if infl_yoy.isna().any() or not np.isfinite(infl_yoy).all():
        raise ValueError(f"{p}: lạm phát phải là số hữu hạn")
    implied = cpi_idx / cpi_idx.shift(12) - 1                  # π_t = CPI_t / CPI_{t−12} − 1 (chỉ số gốc 2010 = 100)
    gap = (implied - infl_yoy).abs().max()
    if gap > 1e-8:
        raise ValueError(f"{p}: cột Inflation_YoY lệch công thức CPI_t/CPI_(t−12) − 1 tới {100 * gap:.4f} điểm %")
    monthly = pd.DataFrame({"CPI_index": cpi_idx, "inflation_yoy": infl_yoy,
                            "inflation_mom": cpi_idx / cpi_idx.shift(1) - 1}, index=df.index)
    monthly["cpi_source"] = "IMF IFS, chỉ số 2010 = 100"
    return monthly


def run(dates: pd.DatetimeIndex | None = None, cfg: dict | None = None) -> pd.DataFrame:
    """Phase 1.4: ghi ``cpi_inflation.csv`` (tháng) và ``inflation_daily.parquet``."""
    cfg = cfg or load_config()
    monthly = load_cpi_cleaned(cfg)
    regimes = classify_regimes(monthly["inflation_yoy"], cfg["inflation"]["threshold"])
    monthly = monthly.join(regimes)
    proc = path_of("processed", cfg)
    monthly.to_csv(proc / "cpi_inflation.csv", encoding="utf-8-sig")
    first = monthly["inflation_yoy"].first_valid_index()
    log.info("Lạm phát YoY từ %s đến %s; tỷ lệ tháng 'Cao' = %.0f%%", first.date(),
             monthly.index.max().date(), 100 * (monthly["regime"] == "Cao").mean())
    if dates is not None:
        cols = ["inflation_yoy", "regime", "regime_median", "regime_tercile"]
        d0 = map_to_daily(monthly[cols], dates, 0)
        d1 = map_to_daily(monthly[cols], dates, cfg["inflation"]["publication_lag_months"]).add_suffix("_pub")
        daily = d0.join(d1)
        daily.index.name = "Date"
        daily.to_parquet(proc / "inflation_daily.parquet")
    return monthly
