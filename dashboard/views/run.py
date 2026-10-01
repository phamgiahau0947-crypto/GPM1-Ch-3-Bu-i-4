"""Vận hành: chạy phân tích và kiểm tra tái lập ngay trong giao diện (không cần gõ lệnh)."""

import pandas as pd
import streamlit as st

from dashboard import ui
from dashboard.common import JOB_LOG, REPRO, follow_job, has_results, job_info, last_run_time, repro_status, run_job


def _follow_running() -> bool:
    """Nếu đang có lần chạy (kể cả bắt đầu trước khi chuyển trang/tải lại), hiện tiến trình của nó. Trả về True nếu có."""
    info = job_info()
    if info is None:
        return False
    st.info(f"**{info.get('label', 'Một lần chạy')}** đang chạy từ {info.get('start', '?')}. Bạn có thể chuyển sang trang khác — "
            "phân tích vẫn chạy tiếp; quay lại trang này để xem tiến trình.")
    code = follow_job()
    (st.success if code == 0 else st.error)("Đã chạy xong." if code == 0 else "Lần chạy báo lỗi — xem nhật ký phía trên.")
    return True


def page_run() -> None:
    current_results = has_results()
    ui.page_header("Chạy phân tích", "Toàn bộ quy trình từ hai file clean trong data/clean đến bảng, hình và báo cáo — bấm một nút, máy tự làm", ic="play")
    ui.kpis([
        {"label": "Trạng thái", "value": "Đã có kết quả" if current_results else "Chưa chạy",
         "note": f"Lần chạy gần nhất: {last_run_time()}" if current_results else "Chưa có kết quả cho nguồn đang chọn",
         "pill": ("good", "sẵn sàng") if current_results else ("warn", "cần chạy")},
        {"label": "Quy trình", "value": "14 bước", "note": "hai file clean → 4 phương pháp → backtest → stress → hình"},
        {"label": "Tái lập", "value": "Seed 2026", "note": "tham số ở config.yaml, không có bước nhập tay"},
    ])
    if _follow_running():
        return
    ui.section("Chọn thao tác", "play")
    c1, c2, c3 = st.columns(3, gap="medium")
    with c1.container(border=True):
        st.markdown("#### 🧮 Tính lại toàn bộ")
        st.caption("Tính lại tất cả dự báo rolling từ dữ liệu clean; bỏ qua cache. Dùng khi muốn xác minh từ đầu hoặc dữ liệu/cấu hình thay đổi. Có thể mất nhiều phút.")
        full = st.button("Bắt đầu chạy toàn bộ", type="primary", width="stretch")
    with c2.container(border=True):
        st.markdown("#### ⚡ Cập nhật kết quả")
        st.caption("Dùng lại dự báo rolling đã lưu nếu còn hợp lệ; tính lại các bảng và hình khác. Thường nhanh hơn lần tính đầu.")
        quick = st.button("Chạy lại nhanh", width="stretch")
    with c3.container(border=True):
        st.markdown("#### 🧪 Kiểm thử đơn vị")
        st.caption("Kiểm thử công thức với giá trị biết trước (VaR/ES Normal, Kupiec, chống look-ahead…). Khoảng 1 phút.")
        tests = st.button("Chạy kiểm thử", width="stretch")
    if full or quick:
        code = run_job(["scripts/run_all.py", "all"] + (["--fresh"] if full else []),
                       "Chạy toàn bộ" if full else "Chạy lại nhanh",
                       total_steps=14)
        if code == 0:
            st.success("Xong! Tiếp theo: **✅ Kiểm tra tái lập**, hoặc xem kết quả ở thanh bên trái.")
    if tests:
        code = run_job(["-m", "pytest", "-q", "--color=no", "tests"], "Kiểm thử đơn vị")
        (st.success if code == 0 else st.error)("Tất cả kiểm thử đều đạt." if code == 0 else "Có kiểm thử không đạt — xem nhật ký.")
    last = JOB_LOG
    if last.exists() and not (full or quick or tests):
        with st.expander("Nhật ký lần chạy gần nhất"):
            st.code("\n".join(last.read_text(encoding="utf-8").splitlines()[-60:]), language="text")


def page_verify() -> None:
    ui.page_header("Kiểm tra tái lập", "So kết quả và mã MD5 hai file clean với bộ tham chiếu của nhóm", ic="check")
    ui.callout("Máy so các chỉ tiêu VaR/ES, backtest, đa dạng hóa, stress test, khuyến nghị và mã MD5 của hai file đầu vào. "
               "Bộ tham chiếu cũ dùng dữ liệu raw không so sánh được; cần rà soát kết quả clean rồi tạo tham chiếu mới.\n"
               "KHỚP: sai lệch ≤ 0,01% · GẦN KHỚP: ≤ 1% (khác biệt số học giữa các loại CPU khi tối ưu GARCH) · LỆCH: > 1%.",
               "Kiểm tra những gì?")
    if not has_results():
        st.warning("Chưa có kết quả để kiểm tra — vào **▶️ Chạy phân tích** trước.")
        return
    if _follow_running():
        return
    if st.button("🔍 Kiểm tra ngay", type="primary"):
        run_job(["scripts/verify_reproducibility.py"], "Kiểm tra tái lập")
    r = repro_status()
    if r is None:
        return
    v = r["kết luận"]
    kind = "good" if v.startswith("KHỚP") else "warn" if v.startswith("GẦN") else "bad"
    counts = r.get("đếm", {})
    ui.kpis([
        {"label": "Kết luận", "value": v.split(" —")[0], "note": v.split("— ")[-1], "pill": (kind, "tái lập"),
         "accent": {"good": ui.T["good"], "warn": ui.T["warn"], "bad": ui.T["bad"]}[kind]},
        {"label": "Khớp tuyệt đối", "value": f"{counts.get('KHỚP', 0)}/{r['số chỉ tiêu']}", "note": "chỉ tiêu"},
        {"label": "Đầu vào khác tham chiếu", "value": r.get("dữ liệu đầu vào không khớp", 0), "note": "file (so mã MD5)",
         "accent": ui.T["good"] if r.get("dữ liệu đầu vào không khớp", 0) == 0 else ui.T["bad"]},
        {"label": "Môi trường", "value": f"Python {r['python']}", "note": f"thời điểm {r['thời điểm']}"},
    ])
    f = REPRO / "chi_tiet_so_khop.csv"
    if f.exists():
        d = pd.read_csv(f, encoding="utf-8-sig")
        if st.toggle("Chỉ hiện chỉ tiêu chưa khớp tuyệt đối", value=False):
            d = d[d["trạng thái"] != "KHỚP"]
        ui.table(d, num=["tham chiếu", "lần chạy này"], height=420)
    html = REPRO / "BAO_CAO_TAI_LAP.html"
    if html.exists():
        st.download_button("⬇️ Tải báo cáo kiểm tra (HTML)", html.read_bytes(), "BAO_CAO_TAI_LAP.html", "text/html")
