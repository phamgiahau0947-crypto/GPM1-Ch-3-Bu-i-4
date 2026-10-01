"""Hình, báo cáo & tải về, thuật ngữ."""

import io
import zipfile

import streamlit as st

from dashboard import ui
from dashboard.common import FIGURES, REPRO, ROOT, TABLES, has_results
from dashboard.texts import GLOSSARY_MD, MODEL_INFO

FIG_TITLES = {
    "F1": "Giá chuẩn hóa", "F2": "Lợi suất theo thời gian", "F3": "Phân phối lợi suất",
    "F4": "QQ-plot", "F5": "Tự tương quan r và r²", "F6": "Lạm phát & chế độ", "F7": "Lợi suất và −VaR99",
    "F8": "Phóng to khủng hoảng", "F9": "Tỷ lệ vi phạm VaR99", "F10": "Tương quan theo thời gian",
    "F11": "Lợi ích đa dạng hóa", "F12": "ES theo tỷ trọng", "F13": "Biến động GARCH", "F14": "p-value Kupiec/Christoffersen",
    "F16": "ES theo lạm phát", "F17": "Component ES", "F18": "Phản ứng xung VAR", "F19": "Tương quan đuôi"}
DOCS = {"Bản nháp báo cáo": "report_draft.md", "Phương pháp luận": "methodology.md",
        "Cẩm nang vấn đáp": "viva_guide.md", "Tổng quan tài liệu": "literature_review.md", "Câu trả lời MT (tự sinh)": "MT_answers.md",
        "Nhật ký sử dụng AI": "ai_usage_log.md", "Hệ thiết kế giao diện": "design_system.md"}


def _zip(paths: list, base) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        for p in paths:
            z.write(p, p.relative_to(base).as_posix())
    return buf.getvalue()


def _key(p) -> tuple:
    k = p.stem.split("_")[0]
    return (int(k[1:].rstrip("b") or 0), p.stem)


def page_figures() -> None:
    ui.page_header("Thư viện hình", "Hình PNG 300 dpi dùng cho báo cáo — nhãn tiếng Việt, vùng xám là giai đoạn stress", ic="chart")
    pngs = sorted(FIGURES.glob("*.png"), key=_key) if has_results() else []
    if not pngs:
        st.warning("Chưa có hình — hãy chạy phân tích.")
        return
    q = st.text_input("Tìm hình", placeholder="ví dụ: F12, backtest, tương quan")
    shown = [p for p in pngs if not q or q.lower() in f"{p.stem} {FIG_TITLES.get(p.stem.split('_')[0].rstrip('b'), '')}".lower()]
    cols = st.columns(2, gap="medium")
    for i, p in enumerate(shown):
        with cols[i % 2].container(border=True):
            st.markdown(f"**{p.stem.split('_')[0]}** · {FIG_TITLES.get(p.stem.split('_')[0].rstrip('b'), p.stem)}")
            st.image(str(p), width="stretch")


def page_docs() -> None:
    ui.page_header("Báo cáo & tải về", "Tài liệu nộp kèm và toàn bộ bảng, hình kết quả", ic="book")
    c1, c2, c3 = st.columns(3)
    tabs_ = [p for p in TABLES.rglob("*") if p.is_file()]
    figs = [p for p in FIGURES.glob("*") if p.is_file()]
    if not has_results():
        tabs_, figs = [], []
    with c1.container(border=True):
        st.markdown("**Bảng kết quả** (CSV, Markdown, LaTeX)")
        st.caption(f"{len(tabs_)} tệp — bảng dữ liệu và phân tích")
        if tabs_:
            st.download_button("⬇️ Tải bảng (.zip)", _zip(tabs_, TABLES.parent), "bang_ket_qua.zip", "application/zip", width="stretch")
    with c2.container(border=True):
        st.markdown("**Hình** (PNG + PDF 300 dpi)")
        st.caption(f"{len(figs)} tệp — hình phân tích hiện hành")
        if figs:
            st.download_button("⬇️ Tải hình (.zip)", _zip(figs, FIGURES.parent), "hinh.zip", "application/zip", width="stretch")
    with c3.container(border=True):
        st.markdown("**Báo cáo kiểm tra tái lập**")
        rep = REPRO / "BAO_CAO_TAI_LAP.html"
        st.caption("HTML, mở bằng trình duyệt")
        if rep.exists():
            st.download_button("⬇️ Tải báo cáo (.html)", rep.read_bytes(), "BAO_CAO_TAI_LAP.html", "text/html", width="stretch")
        else:
            st.caption("Chưa có — chạy Kiểm tra tái lập.")
    ui.section("Đọc tài liệu", "book")
    pick = st.selectbox("Tài liệu", [k for k, v in DOCS.items() if (ROOT / "docs" / v).exists()])
    f = ROOT / "docs" / DOCS[pick]
    text = f.read_text(encoding="utf-8")
    st.download_button(f"⬇️ Tải {DOCS[pick]}", text.encode("utf-8"), DOCS[pick], "text/markdown")
    with st.container(border=True):
        st.markdown(text)


def page_glossary() -> None:
    ui.page_header("Thuật ngữ & tra cứu mô hình", "Giải thích ngắn gọn cho người không chuyên", ic="book")
    with st.container(border=True):
        st.markdown(GLOSSARY_MD)
    ui.section("4 phương pháp VaR/ES theo đề bài", "layers")
    cols = st.columns(2, gap="medium")
    for i, v in enumerate(MODEL_INFO.values()):
        with cols[i % 2].container(border=True):
            st.markdown(v)
