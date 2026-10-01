"""Đọc cấu hình, đường dẫn và tiện ích dùng chung (logging, lưu bảng).

Mọi module trong ``src/market_risk`` lấy tham số qua :func:`load_config`,
không đọc tham số nào hard-code — đảm bảo tái lập (CLAUDE.md §3.3).
"""

from __future__ import annotations

import logging
import sys
from functools import lru_cache
from pathlib import Path

import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[2]

logger = logging.getLogger("market_risk")


@lru_cache(maxsize=4)
def load_config(path: str | None = None) -> dict:
    """Đọc ``config.yaml`` ở gốc repo (hoặc đường dẫn chỉ định)."""
    cfg_path = Path(path) if path else ROOT / "config.yaml"
    with open(cfg_path, encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    return cfg


def path_of(key: str, cfg: dict | None = None) -> Path:
    """Trả về đường dẫn tuyệt đối của một mục trong ``paths`` và tạo thư mục nếu thiếu."""
    cfg = cfg or load_config()
    p = ROOT / cfg["paths"][key]
    p.mkdir(parents=True, exist_ok=True)
    return p


def setup_logging(name: str = "run", level: int = logging.INFO) -> logging.Logger:
    """Ghi log ra màn hình và ``outputs/logs/<name>.log``."""
    log_dir = path_of("logs")
    for stream in (sys.stdout, sys.stderr):      # console Windows (cp1252) không in được tiếng Việt
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    root = logging.getLogger()
    root.handlers.clear()
    fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(name)s | %(message)s", "%H:%M:%S")
    fh = logging.FileHandler(log_dir / f"{name}.log", mode="w", encoding="utf-8")
    sh = logging.StreamHandler()
    for h in (fh, sh):
        h.setFormatter(fmt)
        root.addHandler(h)
    root.setLevel(level)
    for noisy in ("matplotlib", "PIL", "fontTools", "numexpr"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    return logging.getLogger("market_risk")


def save_table(df: pd.DataFrame, name: str, index: bool = False) -> Path:
    """Lưu bảng kết quả vào ``outputs/tables/<name>.csv`` (UTF-8 có BOM để Excel đọc đúng tiếng Việt)."""
    out = path_of("tables") / f"{name}.csv"
    df.to_csv(out, index=index, encoding="utf-8-sig", float_format="%.6g")
    logger.info("Đã lưu bảng %s (%d dòng)", out.name, len(df))
    return out


def read_table(name: str, **kw) -> pd.DataFrame:
    """Đọc lại một bảng đã lưu trong ``outputs/tables``."""
    return pd.read_csv(path_of("tables") / f"{name}.csv", encoding="utf-8-sig", **kw)


def stars(p: float) -> str:
    """Ký hiệu mức ý nghĩa: *** p<0.01, ** p<0.05, * p<0.10."""
    if pd.isna(p):
        return ""
    return "***" if p < 0.01 else "**" if p < 0.05 else "*" if p < 0.10 else ""


def enabled_periods(cfg: dict | None = None, core_only: bool = False) -> dict[str, dict]:
    """Các giai đoạn stress đang bật trong config (tùy chọn chỉ lấy nhóm lõi)."""
    cfg = cfg or load_config()
    per = {k: v for k, v in cfg["stress_periods"].items() if v.get("enabled", True)}
    if core_only:
        per = {k: v for k, v in per.items() if k in cfg["core_stress"]}
    return per


def stress_mask(index: pd.DatetimeIndex, cfg: dict | None = None) -> pd.Series:
    """True nếu ngày thuộc BẤT KỲ giai đoạn stress nào đang bật."""
    m = pd.Series(False, index=index)
    for p in enabled_periods(cfg).values():
        m |= (index >= p["start"]) & (index <= p["end"])
    return m
