"""Chạy toàn bộ đề án từ hai file clean đến bảng, hình và bản nháp diễn giải — KHÔNG tương tác.

    python scripts/run_all.py all        # toàn bộ (tương đương `make all`)
    python scripts/run_all.py data       # Phase 1
    python scripts/run_all.py run        # Phase 2–9 (cần data)
    python scripts/run_all.py report     # Phase 10–11: hình + xuất Markdown/LaTeX
    python scripts/run_all.py all --fresh   # xóa cache rolling trước khi chạy
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from market_risk import (  # noqa: E402
    application,
    data_pipeline,
    descriptive,
    diversification,
    fx_inflation,
    inflation,
    overall,
    plots,
    portfolio,
    reporting,
    rolling,
    spillover,
    stress,
)
from market_risk.backtest import runner as backtest  # noqa: E402
from market_risk.config import load_config, path_of, setup_logging  # noqa: E402


def step(log, name: str, fn, answers: dict | None = None, key: str | None = None):
    t0 = time.perf_counter()
    log.info("=== %s ===", name)
    out = fn()
    log.info("--- %s xong sau %.1f giây", name, time.perf_counter() - t0)
    if answers is not None and key and isinstance(out, str):
        answers[key] = out
        log.info("\n%s", out)
    return out


def do_data(log, cfg):
    prices = step(log, "Phase 1.3 — dữ liệu giá", lambda: data_pipeline.run(cfg))
    step(log, "Phase 1.4 — lạm phát từ CPI", lambda: inflation.run(prices.index, cfg))
    step(log, "Phase 1.5 — lợi suất & danh mục", lambda: portfolio.run(prices, cfg))


def do_run(log, cfg):
    ans: dict[str, str] = {}
    step(log, "Phase 2 — thống kê mô tả & kiểm định giả định", lambda: descriptive.run(cfg=cfg), ans, "Kiem_dinh_gia_dinh")
    step(log, "Phase 4 — rolling", lambda: rolling.run(cfg))
    step(log, "Phase 3 — bảng toàn kỳ (MT1)", lambda: overall.run(cfg), ans, "MT1")
    step(log, "Phase 5 — backtest (MT4)", lambda: backtest.run(cfg=cfg))
    step(log, "Phase 6 — đa dạng hóa (MT2)", lambda: diversification.run(cfg), ans, "MT2")
    step(log, "Phase 7 — tỷ giá & lạm phát (MT3)", lambda: fx_inflation.run(cfg), ans, "MT3")
    step(log, "Bài 9 — VAR/Granger/IRF", lambda: spillover.run(cfg), ans, "VAR_lan_toa")
    step(log, "Phase 8 — stress test (MT5)", lambda: stress.run(cfg), ans, "MT5")
    step(log, "Phase 9 — Application", lambda: application.run(cfg))
    reporting.write_answers(ans, cfg)


def do_report(log, cfg):
    step(log, "Phase 10 — hình", lambda: plots.run(cfg))
    step(log, "Phase 11.4 — xuất bảng Markdown/LaTeX", lambda: reporting.run(cfg))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("target", choices=["data", "run", "report", "all"], nargs="?", default="all")
    ap.add_argument("--fresh", action="store_true", help="xóa cache rolling")
    args = ap.parse_args()
    cfg = load_config()
    log = setup_logging(f"run_{args.target}")
    if args.fresh:
        shutil.rmtree(path_of("processed", cfg) / "rolling_cache", ignore_errors=True)
    t0 = time.perf_counter()
    if args.target in ("data", "all"):
        do_data(log, cfg)
    if args.target in ("run", "all"):
        do_run(log, cfg)
    if args.target in ("report", "all"):
        do_report(log, cfg)
    if args.target == "all":
        clean_dir = ROOT / cfg["cleaned_files"]["directory"]
        inputs = {
            key: hashlib.md5((clean_dir / cfg["cleaned_files"][key]).read_bytes()).hexdigest()
            for key in ("daily", "cpi")
        }
        run_manifest = ROOT / "outputs" / "last_successful_run.json"
        run_manifest.write_text(json.dumps({
            "data_source": "cleaned",
            "models_main": cfg["models_main"],
            "backtests": ["Kupiec", "Christoffersen"],
            "input_hashes": inputs,
            "completed_at": datetime.now().isoformat(timespec="seconds"),
        }, ensure_ascii=False, indent=2), encoding="utf-8")
    log.info("HOÀN TẤT '%s' sau %.1f phút", args.target, (time.perf_counter() - t0) / 60)


if __name__ == "__main__":
    main()
