"""Hai file clean đầu vào và các chuỗi dẫn xuất trong pipeline."""

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard import ui
from dashboard.common import PROCESSED, need_results, pq, stress_shapes, style, tbl
from market_risk.config import load_config


def page() -> None:
    cfg = load_config()
    src = [
        ("Giá ngày", cfg["cleaned_files"]["daily"], "02/2006 → 02/2025",
         "Investing.com — giá đóng cửa VN-Index (HOSE), S&P 500, USD/VND; S&P 500 khớp FRED (T0b)"),
        ("CPI & lạm phát", cfg["cleaned_files"]["cpi"], "01/2006 → 07/2026",
         "IMF IFS — CPI tháng, gốc 2010 = 100; chỉ dùng để phân loại bối cảnh lạm phát"),
    ]
    subtitle = "Mô hình chỉ dùng hai file clean trong data/clean; giá S&P 500 được đối chiếu với chuỗi FRED SP500."
    ui.page_header("Dữ liệu đầu vào", subtitle, ic="db")
    rows = "".join(f"<tr><td style='padding:10px 12px'><b>{a}</b></td><td style='padding:10px 12px'>{b}</td>"
                   f"<td style='padding:10px 12px;white-space:nowrap'>{c}</td><td style='padding:10px 12px;color:{ui.T['text2']}'>{d}</td></tr>"
                   for a, b, c, d in src)
    st.html(f"<div class='mr-card' style='padding:4px 6px'><table style='width:100%;border-collapse:collapse;font-size:14px'>"
            f"<thead><tr style='text-align:left;color:{ui.T['muted']};font-size:12px;text-transform:uppercase;letter-spacing:.06em'>"
            "<th style='padding:10px 12px'>Chuỗi</th><th style='padding:10px 12px'>Nguồn</th><th style='padding:10px 12px'>Giai đoạn</th>"
            f"<th style='padding:10px 12px'>Nguồn & kiểm chứng</th></tr></thead><tbody>{rows}</tbody></table></div>")
    if need_results():
        return
    q = tbl("T0_data_quality")
    m = q[q["series"] == "MERGED (inner)"].iloc[0]
    n_fx = int(q.loc[q["series"] == "USDVND", "n_flagged_errors"].iloc[0])
    items = [{"label": "Phiên giá", "value": f"{int(m['N_clean']):,}".replace(",", "."), "note": "từ file giá clean"},
             {"label": "Điểm lỗi tỷ giá đã lọc", "value": n_fx, "note": "giá lệch rồi quay về ngay (12/2009)"}]
    fred = tbl("T0b_fred_sp500_check")
    if fred is not None:
        f = fred.iloc[0]
        items.append({"label": "S&P 500 so với FRED", "value": f"{f['max_abs_diff_pct']:.4f}%".replace(".", ","),
                      "note": f"lệch tối đa trên {int(f['n_common']):,} phiên từ {pd.Timestamp(f['start']):%d/%m/%Y} (T0b)".replace(",", "."),
                      "pill": ("good", "khớp FRED SP500") if f["max_abs_diff_pct"] < 0.01 else ("warn", "kiểm tra lại")})
    ui.kpis(items)

    t1, t2, t3, t4 = st.tabs(["Giá & lợi suất", "Chất lượng dữ liệu", "Lọc tỷ giá", "Lạm phát"])
    prices = pq("daily_prices.parquet")
    with t1:
        norm = pd.DataFrame({"VN-Index": prices["VN"], "S&P 500 (USD)": prices["SP_USD"],
                             "S&P 500 quy đổi VND": prices["SP_USD"] * prices["USDVND"]})
        fig = px.line(100 * norm / norm.iloc[0], log_y=True, labels={"value": "Chỉ số (ngày đầu = 100, thang log)", "Date": "", "variable": ""})
        st.plotly_chart(stress_shapes(style(fig, 440, title="Giá chuẩn hóa — vùng xám là giai đoạn stress")), width="stretch")
        s = st.segmented_control("Lợi suất ngày của", ["VN", "SP_USD", "USDVND"], default="VN",
                                 format_func={"VN": "VN-Index", "SP_USD": "S&P 500 (USD)", "USDVND": "Tỷ giá USD/VND"}.get)
        r = np.log(prices[s or "VN"]).diff().dropna()
        fig = go.Figure(go.Scatter(x=r.index, y=r, mode="lines", line=dict(width=0.7, color=ui.SERIES[0]), name="Lợi suất log"))
        st.plotly_chart(stress_shapes(style(fig, 300, pct=True)), width="stretch")
    with t2:
        ui.table(q, pct=["pct_dropped_by_merge"], rename={"series": "Chuỗi", "N_raw": "Số dòng gốc", "N_clean": "Sau làm sạch",
                 "n_flagged_errors": "Điểm lỗi", "start": "Từ", "end": "Đến", "n_missing": "Ô thiếu", "n_dup_dates": "Ngày trùng",
                 "dropped_by_merge": "Mất khi ghép", "pct_dropped_by_merge": "% mất khi ghép"})
        st.markdown("**10 biến động ngày lớn nhất mỗi chuỗi** (dò lỗi nhập liệu)")
        ui.table(tbl("T0_top_moves"), pct=["log_return"], rename={"series": "Chuỗi", "Date": "Ngày", "log_return": "Lợi suất",
                 "rank": "Hạng", "alert": "Vượt ngưỡng"})
    with t3:
        st.markdown("Bộ lọc Hampel: điểm lệch hơn 1,5% so với trung vị 15 phiên (giá lệch rồi quay về ngay) được thay bằng giá "
                    "hợp lệ liền trước. Các đợt điều chỉnh tỷ giá thật (26/11/2009, 11/02/2010, 11/02/2011) giữ mức mới nên không bị lọc.")
        ui.table(tbl("T0_fx_cleaning_log"), rename={"series": "Chuỗi", "Date": "Ngày", "value": "Giá bị lọc", "rule": "Quy tắc",
                 "action": "Xử lý"})
    with t4:
        mth = pd.read_csv(PROCESSED / "cpi_inflation.csv", index_col=0, parse_dates=True, encoding="utf-8-sig")
        fig = go.Figure()
        fig.add_scatter(x=mth.index, y=mth["inflation_yoy"], name="Lạm phát so cùng kỳ", line=dict(color=ui.SERIES[3], width=2))
        fig.add_hline(y=0.04, line_dash="dash", line_color=ui.T["muted"], annotation_text="ngưỡng 4%")
        st.plotly_chart(style(fig, 380, pct=True, title="Lạm phát Việt Nam tính từ CPI"), width="stretch")
        st.caption("Chế độ “Cao” khi lạm phát > 4% (gần mục tiêu điều hành, ≈ trung vị). Chỉ để chia bối cảnh — không đi vào VaR ngày.")
