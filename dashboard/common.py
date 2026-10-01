"""Tiện ích dùng chung cho giao diện: đường dẫn, đọc kết quả (có cache), trạng thái, chạy tiến trình nền."""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from market_risk.config import enabled_periods, load_config  # noqa: E402
from market_risk.models import MODEL_LABELS, MODEL_TIER  # noqa: E402

TABLES = ROOT / "outputs" / "tables"
FIGURES = ROOT / "outputs" / "figures"
PROCESSED = ROOT / "data" / "processed"
LOGS = ROOT / "outputs" / "logs"
REPRO = ROOT / "outputs" / "reproducibility"
LOCK = LOGS / "dang_chay.lock"

PORT_LABEL = {"VN100": "100% VN-Index", "VN50_SP50": "50% VN · 50% S&P", "SP100": "100% S&P 500 (VND)",
              "W75_25": "75/25", "W25_75": "25/75"}
OKABE = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#56B4E9", "#F0E442", "#000000"]
CFG = load_config()
ANSI = re.compile(r"\x1b\[[0-9;]*m")


def periods() -> dict[str, tuple]:
    return {"Toàn kỳ": (None, None)} | {v["label"]: (v["start"], v["end"]) for v in enabled_periods(CFG).values()}


def stress_shapes(fig: go.Figure) -> go.Figure:
    """Tô xám các giai đoạn stress trên biểu đồ chuỗi thời gian."""
    for p in enabled_periods(CFG).values():
        fig.add_vrect(x0=p["start"], x1=p["end"], fillcolor="#8C99AE", opacity=0.13, line_width=0, layer="below")
    return fig


def style(fig: go.Figure, height: int = 420, pct: bool = False, title: str | None = None) -> go.Figure:
    """Áp template ngân hàng thống nhất (xem dashboard/ui.py)."""
    from dashboard import ui

    return ui.style(fig, height=height, pct=pct, title=title)


def has_results() -> bool:
    marker = ROOT / "outputs" / "last_successful_run.json"   # nằm ngoài logs/ để bản nộp không cần kèm nhật ký
    if not (PROCESSED / "rolling_forecasts.parquet").exists() or not (TABLES / "T15_model_recommendation.csv").exists():
        return False
    try:
        run = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    if run.get("data_source") != "cleaned":
        return False
    if run.get("models_main") != CFG["models_main"]:
        return False
    if run.get("backtests") != ["Kupiec", "Christoffersen"]:
        return False
    try:
        input_hashes = {
            key: hashlib.md5((ROOT / CFG["cleaned_files"]["directory"] / CFG["cleaned_files"][key]).read_bytes()).hexdigest()
            for key in ("daily", "cpi")
        }
    except OSError:
        return False
    return run.get("input_hashes") == input_hashes


def last_run_time() -> str | None:
    f = TABLES / "T15_model_recommendation.csv"
    return dt.datetime.fromtimestamp(f.stat().st_mtime).strftime("%H:%M %d/%m/%Y") if f.exists() else None


@st.cache_data(show_spinner=False)
def table(name: str, _mtime: float | None = None) -> pd.DataFrame:
    return pd.read_csv(TABLES / f"{name}.csv", encoding="utf-8-sig")


def tbl(name: str) -> pd.DataFrame | None:
    """Đọc bảng kết quả; trả về None nếu chưa có (giao diện sẽ báo cần chạy phân tích)."""
    f = TABLES / f"{name}.csv"
    if not f.exists():
        return None
    return table(name, f.stat().st_mtime)


@st.cache_data(show_spinner=False)
def parquet(name: str, _mtime: float | None = None) -> pd.DataFrame:
    return pd.read_parquet(PROCESSED / name)


def pq(name: str) -> pd.DataFrame | None:
    f = PROCESSED / name
    if not f.exists():
        return None
    return parquet(name, f.stat().st_mtime)


def need_results() -> bool:
    """Hiện hướng dẫn nếu chưa có kết quả. Trả về True nếu trang nên dừng."""
    if has_results():
        return False
    st.warning("Chưa có kết quả phân tích. Vào trang **▶️ Chạy phân tích** và bấm **Bắt đầu chạy toàn bộ**. "
               "Lần đầu có thể mất nhiều phút.")
    return True


def repro_status() -> dict | None:
    f = REPRO / "ket_qua_kiem_tra.json"
    if not f.exists():
        return None
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


JOB_LOG = LOGS / "giao_dien_lan_chay_cuoi.log"


def _pid_alive(pid: int) -> bool:
    try:
        if sys.platform.startswith("win"):
            out = subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True).stdout
            return str(pid) in out and "python" in out.lower()   # PID có thể bị Windows cấp lại cho tiến trình khác
        import os

        os.kill(pid, 0)
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def job_info() -> dict | None:
    """Thông tin lần chạy đang diễn ra (pid, tên, số bước) hoặc None. Tự dọn khóa của tiến trình đã kết thúc."""
    if not LOCK.exists():
        return None
    try:
        info = json.loads(LOCK.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        LOCK.unlink(missing_ok=True)
        return None
    if not _pid_alive(int(info.get("pid", -1))):
        LOCK.unlink(missing_ok=True)
        return None
    return info


def is_running() -> bool:
    return job_info() is not None


def start_job(args: list[str], label: str, total_steps: int | None = None) -> subprocess.Popen:
    """Khởi động lệnh Python ở thư mục dự án; nhật ký ghi thẳng ra file nên tiến trình KHÔNG phụ thuộc trang đang mở
    (người dùng chuyển trang hoặc tải lại trang thì phân tích vẫn chạy tiếp và có thể theo dõi lại)."""
    import os

    LOGS.mkdir(parents=True, exist_ok=True)
    cmd = [sys.executable, "-X", "utf8", *args]
    env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONUNBUFFERED": "1", "NO_COLOR": "1", "PY_COLORS": "0"}
    with open(JOB_LOG, "w", encoding="utf-8") as fh:
        proc = subprocess.Popen(cmd, cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT, env=env)
    LOCK.write_text(json.dumps({"pid": proc.pid, "label": label, "total_steps": total_steps,
                                "start": dt.datetime.now().strftime("%H:%M:%S")}, ensure_ascii=False), encoding="utf-8")
    return proc


def _log_lines() -> list[str]:
    if not JOB_LOG.exists():
        return []
    text = JOB_LOG.read_text(encoding="utf-8", errors="replace")
    return [ANSI.sub("", ln).rstrip() for ln in text.splitlines() if ln.strip()]   # bỏ mã màu của terminal


def follow_job(proc: subprocess.Popen | None = None) -> int:
    """Hiển thị thanh tiến trình + nhật ký trực tiếp cho tới khi lần chạy kết thúc; trả về mã kết thúc (0 = thành công).

    Tiến trình được tính theo số dòng '=== … ===' mà scripts/run_all.py in ra ở đầu mỗi bước.
    """
    import time

    info = job_info() or {}
    label, total = info.get("label", "Đang chạy"), info.get("total_steps")
    bar = st.progress(0.0, text=f"{label}: đang khởi động…")
    box = st.empty()
    while True:
        lines = _log_lines()
        steps = [ln.split("=== ")[-1].replace(" ===", "") for ln in lines if "=== " in ln]
        if total and steps:
            bar.progress(min(len(steps) / total, 0.99), text=f"{label}: bước {len(steps)}/{total} — {steps[-1]}")
        if lines:
            box.code("\n".join(lines[-18:]), language="text")
        alive = proc.poll() is None if proc is not None else is_running()
        if not alive:
            break
        time.sleep(1.0)
    lines = _log_lines()
    if proc is not None:
        code = proc.wait()
    else:   # theo dõi lại một lần chạy bắt đầu từ lượt tải trang trước: suy ra kết quả từ nhật ký
        code = 1 if any(k in ln for ln in lines[-40:] for k in ("Traceback", " failed", "Error:")) else 0
    LOCK.unlink(missing_ok=True)
    box.code("\n".join(lines[-18:]), language="text")
    if code == 0:
        bar.progress(1.0, text=f"{label}: HOÀN TẤT ✅")
    else:
        bar.progress(1.0, text=f"{label}: LỖI (mã {code}) ❌ — xem nhật ký bên dưới")
    st.cache_data.clear()
    return code


def run_job(args: list[str], label: str, total_steps: int | None = None) -> int:
    """Chạy một lệnh và theo dõi tới khi xong (xem start_job, follow_job)."""
    return follow_job(start_job(args, label, total_steps))


def fmt_pct(x, d: int = 2) -> str:
    return "" if pd.isna(x) else f"{100 * x:.{d}f}%".replace(".", ",")


def mt_answers() -> dict[str, str]:
    """Đọc các đoạn trả lời tự sinh (docs/MT_answers.md) thành dict {mục: nội dung}."""
    f = ROOT / "docs" / "MT_answers.md"
    if not f.exists():
        return {}
    out, key = {}, None
    for line in f.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            key = line[3:].strip()
            out[key] = ""
        elif key:
            out[key] += line + "\n"
    return {k: v.strip() for k, v in out.items()}


__all__ = ["MODEL_LABELS", "MODEL_TIER", "CFG", "ROOT"]
