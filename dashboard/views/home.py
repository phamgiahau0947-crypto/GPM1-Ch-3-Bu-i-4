"""Bảng điều khiển: tóm tắt đề án theo bố cục slide của giảng viên + KPI + kết luận từng mục tiêu."""

import streamlit as st

from dashboard import ui
from dashboard.common import has_results, last_run_time, repro_status, tbl
from market_risk.models import MODEL_LABELS


def _kpis() -> None:
    t4, t15, q = tbl("T4_var_es_overall"), tbl("T15_model_recommendation"), tbl("T0_data_quality")
    items = []
    if t4 is not None:
        c = t4[t4["sample"] == "common"].pivot(index="model", columns="portfolio", values="ES_975")
        red = (1 - c["VN50_SP50"] / c["VN100"]) * 100
        items.append({"label": "Giảm rủi ro đuôi khi 50/50", "value": ui.num(red.median(), 1, "%"),
                      "note": f"ES 97,5% so với 100% VN — thấp hơn ở {int((red > 0).sum())}/{len(red)} mô hình",
                      "accent": ui.T["gold500"]})
    if t15 is not None:
        b = t15.iloc[0]
        n_ok = int(b["n_pass_var99"])
        items.append({"label": "Mô hình xếp hạng đầu", "value": b["label"].split(" (")[0],
                      "note": f"Đạt cả Kupiec và Christoffersen (VaR 99%) ở {n_ok}/3 danh mục",
                      "pill": ("good", "được backtest ủng hộ") if n_ok >= 2 else ("warn", "chưa đạt cả hai kiểm định"),
                      "accent": ui.T["good"] if n_ok >= 2 else ui.T["warn"]})
    r = repro_status()
    if r:
        kind = "good" if r["kết luận"].startswith("KHỚP") else "warn" if r["kết luận"].startswith("GẦN") else "bad"
        items.append({"label": "Kiểm tra tái lập", "value": r["kết luận"].split(" —")[0],
                      "note": f"{r['số chỉ tiêu']} chỉ tiêu · {r['thời điểm']}", "pill": (kind, "đối chiếu bộ số của nhóm"),
                      "accent": ui.T["good"] if kind == "good" else ui.T["warn"]})
    else:
        items.append({"label": "Kiểm tra tái lập", "value": "Chưa kiểm tra", "note": "Vào ✅ Kiểm tra tái lập", "pill": ("info", "1 phút")})
    if q is not None:
        m = q[q["series"] == "MERGED (inner)"].iloc[0]
        items.append({"label": "Dữ liệu", "value": f"{int(m['N_clean']):,} phiên".replace(",", "."),
                      "note": f"{str(m['start'])[:7].replace('-', '/')} → {str(m['end'])[:7].replace('-', '/')} · 2 file clean"})
    ui.kpis(items)


def page() -> None:
    ui.page_header("Đo lường rủi ro thị trường: VaR, ES và kiểm định ngược",
                   "Market Risk Measurement & Backtesting — danh mục VN-Index / S&P 500 quy đổi VND · hai file clean")
    if has_results():
        _kpis()
        st.caption(f"Kết quả cập nhật lúc {last_run_time()}.")
    else:
        st.warning("Chưa có kết quả phân tích — mở **▶️ Chạy phân tích** rồi chọn **Bắt đầu chạy toàn bộ**. "
                   "Lần đầu có thể mất nhiều phút.")
        return

    col1, col2 = st.columns([1.45, 1], gap="large")
    with col1:
        ui.check_card("Nội dung cốt lõi", [
            "Danh mục kết hợp <b>VN-Index và S&amp;P 500</b> quy đổi VND; đầu vào là hai file clean trong data/clean",
            "Ước lượng VaR/ES bằng bốn phương pháp trong phạm vi đề: HS, Normal, MC_Normal và GARCH_N",
            "Mô hình biến động có điều kiện <b>GARCH(1,1)</b>; tính <b>Expected Shortfall 97,5%</b> theo FRTB",
            "Kiểm định <b>Kupiec và Christoffersen</b>; <b>stress test</b> các giai đoạn 2008, 2018, 2020, 2022",
        ])
    with col2:
        rec = tbl("T15_model_recommendation")
        best = MODEL_LABELS.get(rec.iloc[0]["model"], "") if rec is not None else "—"
        ui.navy_panel("Mục tiêu đề án", [
            ("Thành thạo quy trình đo lường rủi ro thị trường tại ngân hàng",
             "Quy trình tự động: dữ liệu → 4 phương pháp → Kupiec/Christoffersen → stress test."),
            ("Đánh giá độ tin cậy của mô hình bằng kiểm định thống kê",
             "Kiểm định giả định (chuẩn, dừng, ARCH) và backtest VaR bằng Kupiec, Christoffersen."),
            ("Đưa ra khuyến nghị lựa chọn mô hình cho nhà quản trị rủi ro", f"Xếp hạng đầu: <b>{best}</b> — xem trang Khuyến nghị và báo cáo."),
        ])

    ui.section("Bắt đầu nhanh", "play", "cho người chấm — không cần gõ lệnh")
    c1, c2, c3 = st.columns(3)
    for col, (target, label, ic) in zip((c1, c2, c3), [
            ("chay", "1 · Chạy phân tích", "▶️"), ("tai-lap", "2 · Kiểm tra tái lập", "✅"),
            ("tai-ve", "3 · Tải báo cáo & kết quả", "📦")]):
        col.page_link(st.session_state["_pages"][target], label=label, icon=ic, width="stretch")

    ui.section("Kết luận theo mục tiêu nghiên cứu", "target")
    t4, t8, t9, t5, t11 = (tbl(n) for n in ("T4_var_es_overall", "T8_diversification_by_corr", "T9_fx_effect",
                                            "T5b_pass_table", "T11_stress_historical"))
    if t4 is None:
        return
    cards = []
    c = t4[t4["sample"] == "common"].pivot(index="model", columns="portfolio", values="ES_975")
    cards.append(("MT1 · Rủi ro danh mục", f"50/50 có ES thấp hơn 100% VN ở {int(((1 - c['VN50_SP50'] / c['VN100']) > 0).sum())}/4 phương pháp; "
                  f"lựa chọn mô hình làm ES của 100% VN chênh tới {ui.num(100 * (c['VN100'].max() - c['VN100'].min()), 1)} điểm %/ngày.", "mt1"))
    if t5 is not None:
        full = t5[t5["pass_all"]].groupby("model").size().sort_values(ascending=False)
        top = ", ".join(f"{MODEL_LABELS[m]} ({n}/3)" for m, n in full.items()) or "không có"
        cards.append(("MT4 · Độ tin cậy mô hình", f"Không bị bác bỏ bởi cả Kupiec và Christoffersen ở VaR 99%: {top}.", "mt4"))
    if t8 is not None:
        d = t8[(t8["model"] == "GARCH_N") & (t8["metric"] == "DR") & (t8["corr_measure"] == "corr_252")].set_index("tercile")["mean"]
        cards.append(("MT2 · Đa dạng hóa", f"Lợi ích giảm ES {100 * d['Thấp']:.0f}% khi tương quan thấp, còn {100 * d['Cao']:.0f}% khi tương "
                      "quan cao — thu hẹp nhưng không biến mất.", "mt2"))
    if t9 is not None:
        f = t9[(t9["period"] == "Toàn kỳ") & (t9["portfolio"] == "100% S&P")]["dES_FX"] * 100
        cards.append(("MT3 · Tỷ giá & lạm phát", f"Quy đổi VND làm ES đổi {ui.num(f.min(), 2, sign=True)} → {ui.num(f.max(), 2, sign=True)} điểm %: tỷ giá gần như không thêm "
                      "rủi ro đuôi; rủi ro cao hơn trong bối cảnh lạm phát > 4%.", "mt3"))
    if t11 is not None:
        u = t11[t11["period"].isin(["GFC_2008", "TradeWar_2018", "COVID_2020", "Tightening_2022"])].groupby("model")["UR_VaR99"].mean()
        cards.append(("MT5 · Stress test", f"Khi khủng hoảng, {MODEL_LABELS[u.idxmax()]} vi phạm VaR99 gấp {ui.num(u.max(), 1)} lần kỳ vọng; "
                      f"{MODEL_LABELS[u.idxmin()]} chỉ {ui.num(u.min(), 1)} lần.", "mt5"))
    cols = st.columns(len(cards))
    for col, (title, text, target) in zip(cols, cards):
        with col.container(border=True, height=210):
            st.markdown(f"**{title}**")
            st.caption(text)
            st.page_link(st.session_state["_pages"][target], label="Xem chi tiết", icon="➡️")
    ui.source_bar()
