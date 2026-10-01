"""Giao diện Đề án 03 — VaR, ES & Backtesting (Streamlit, nhiều trang, phong cách hệ thống ngân hàng).

Cách mở dễ nhất (Windows): nhấp đúp `CHAY_DU_AN.bat` ở thư mục gốc.
Hoặc: `python -m streamlit run dashboard/app.py` (chạy từ thư mục gốc để nạp theme và font trong .streamlit/config.toml).
"""

import sys
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT, ROOT / "src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

st.set_page_config(page_title="Đề án 03 — Quản trị rủi ro thị trường", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

from dashboard import ui  # noqa: E402
from dashboard.views import application, data, guide, home, library, results, run  # noqa: E402

ui.inject_css()
ui.logo()

P = {
    "huong-dan": st.Page(guide.page, title="Hướng dẫn sử dụng", icon=":material/help_outline:", url_path="huong-dan", default=True),
    "trang-chu": st.Page(home.page, title="Bảng điều khiển", icon=":material/space_dashboard:", url_path="trang-chu"),
    "chay": st.Page(run.page_run, title="Chạy phân tích", icon=":material/play_circle:", url_path="chay"),
    "tai-lap": st.Page(run.page_verify, title="Kiểm tra tái lập", icon=":material/verified:", url_path="tai-lap"),
    "du-lieu": st.Page(data.page, title="Dữ liệu", icon=":material/database:", url_path="du-lieu"),
    "mt1": st.Page(results.page_mt1, title="MT1 · Rủi ro & mô hình", icon=":material/bar_chart:", url_path="mt1"),
    "mt4": st.Page(results.page_backtest, title="MT4 · Backtest", icon=":material/rule:", url_path="mt4"),
    "mt2": st.Page(results.page_mt2, title="MT2 · Đa dạng hóa", icon=":material/hub:", url_path="mt2"),
    "mt3": st.Page(results.page_mt3, title="MT3 · Tỷ giá & lạm phát", icon=":material/currency_exchange:", url_path="mt3"),
    "mt5": st.Page(results.page_mt5, title="MT5 · Stress test", icon=":material/warning:", url_path="mt5"),
    "application": st.Page(application.page, title="Khuyến nghị", icon=":material/recommend:", url_path="application"),
    "hinh": st.Page(library.page_figures, title="Thư viện hình", icon=":material/image:", url_path="hinh"),
    "tai-ve": st.Page(library.page_docs, title="Báo cáo & tải về", icon=":material/download:", url_path="tai-ve"),
    "thuat-ngu": st.Page(library.page_glossary, title="Thuật ngữ", icon=":material/menu_book:", url_path="thuat-ngu"),
}
st.session_state["_pages"] = P
nav = st.navigation({
    "Bắt đầu": [P["huong-dan"], P["trang-chu"]],
    "Vận hành": [P["chay"], P["tai-lap"]],
    "Kết quả nghiên cứu": [P[k] for k in ("du-lieu", "mt1", "mt4", "mt2", "mt3", "mt5", "application")],
    "Tài liệu": [P["hinh"], P["tai-ve"], P["thuat-ngu"]],
}, expanded=True)   # hiện đủ 14 trang, không ẩn sau "View more"
st.sidebar.caption("Seed 2026 · tham số ở config.yaml\n\nNguồn: Investing.com · IMF IFS · đối chiếu FRED")
nav.run()
