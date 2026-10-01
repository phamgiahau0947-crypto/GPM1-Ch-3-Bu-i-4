"""Khuyến nghị: lưới tỷ trọng so với giới hạn ES, khuyến nghị lựa chọn mô hình, thử tỷ trọng tùy ý."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard import ui
from dashboard.common import CFG, MODEL_LABELS, PORT_LABEL, ROOT, need_results, pq, stress_shapes, style, tbl
from market_risk.portfolio import portfolio_return

ORDER = ["100/0", "75/25", "50/50", "25/75", "0/100"]
AUTO_MODEL = "__auto__"


@st.cache_data(show_spinner=False)
def _weighted_forecast(returns: pd.Series, model: str, window: int, cfg: dict) -> pd.DataFrame:
    """Tính dự báo rolling cho tỷ trọng tùy ý, dùng cache theo chuỗi, mô hình, cửa sổ và cấu hình."""
    from market_risk.rolling import COLS, rolling_forecast

    forecast, _ = rolling_forecast(
        returns.to_numpy(dtype=float),
        model,
        window,
        cfg["risk"]["garch_refit_every"],
        cfg,
    )
    return pd.DataFrame(forecast, index=returns.index, columns=COLS)


def _recommendation() -> None:
    rec = tbl("T15_model_recommendation")
    rows = []
    for r in rec.itertuples():
        kind = "good" if r.n_pass_var99 >= 2 else "warn" if r.n_pass_var99 == 1 else "bad"
        short = {"good": "Mô hình chính", "warn": "Bổ trợ / giám sát", "bad": "Chỉ đối chứng"}.get(kind, "")
        rows.append(f"<tr><td style='padding:10px 12px;font:700 16px Montserrat;color:{ui.T['navy800']}'>{int(r.overall_rank)}</td>"
                    f"<td style='padding:10px 12px'><b>{r.label}</b> <span style='color:{ui.T['muted']}'>{r.tier}</span></td>"
                    f"<td style='padding:10px 12px'>{int(r.n_pass_var99)}/3</td>"
                    f"<td style='padding:10px 12px'>{ui.num(r.crisis_UR_VaR99, 1)}×</td>"
                    f"<td style='padding:10px 12px'>{ui.pill(kind, short)}</td></tr>")
    st.html(f"<div class='mr-card' style='padding:4px 6px'><table style='width:100%;border-collapse:collapse;font-size:14px'><thead>"
            f"<tr style='text-align:left;color:{ui.T['muted']};font-size:12px;text-transform:uppercase;letter-spacing:.06em'>"
            "<th style='padding:10px 12px'>Hạng</th><th style='padding:10px 12px'>Mô hình</th><th style='padding:10px 12px'>Đạt cả hai · VaR99</th>"
            "<th style='padding:10px 12px'>Vi phạm/kỳ vọng khi stress</th>"
            f"<th style='padding:10px 12px'>Khuyến nghị</th></tr></thead><tbody>{''.join(rows)}</tbody></table></div>")
    st.caption("Xếp hạng mô tả dựa trên số danh mục không bị bác bỏ bởi cả Kupiec và Christoffersen ở VaR 99%, "
               "mức vi phạm trong giai đoạn stress, độ phức tạp và khả năng giải thích. Không kiểm định ES hay so sánh thống kê giữa mô hình.")
    t13 = tbl("T13_robustness")
    if t13 is not None:
        ok = t13[(t13["p_uc"] >= 0.05) & (t13["p_cc"] >= 0.05)]
        if len(ok):
            names = "; ".join(f"{MODEL_LABELS.get(r.model, r.model)}, cửa sổ {int(r.window)} phiên, {PORT_LABEL.get(r.portfolio, r.portfolio)} "
                              f"({int(r.x)} vi phạm, {100 * r.rate:.2f}%)".replace(".", ",") for r in ok.itertuples())
            ui.callout(f"Trong {len(t13)} cấu hình robustness (T13), chỉ có cấu hình sau được cả Kupiec và Christoffersen ủng hộ ở VaR 99%: "
                       f"**{names}**. Cửa sổ dài chứa nhiều cú sốc hơn nên VaR ít \"quên\" rủi ro sau giai đoạn yên ổn — "
                       "gợi ý dùng HS với cửa sổ dài làm thước đo chính, GARCH(1,1) làm tín hiệu cảnh báo sớm.",
                       "Phát hiện từ kiểm tra độ vững")


def page() -> None:
    ui.page_header("Khuyến nghị cho nhà quản trị rủi ro", "Lựa chọn mô hình · phân bổ VN/Mỹ so với giới hạn ES (định hướng, không nêu % cụ thể)", ic="target")
    if need_results():
        return
    t14, rec = tbl("T14_allocation_es_limits"), tbl("T15_model_recommendation")
    recommended_model = str(rec.iloc[0]["model"])
    m = recommended_model
    n_pass = int(rec.iloc[0]["n_pass_var99"])
    pass_kind = "good" if n_pass >= 2 else "warn" if n_pass == 1 else "bad"
    d = t14[t14["model"] == m]
    base = d.set_index(["weight", "period"])["ES_mean"]
    ui.kpis([
        {"label": "Mô hình đứng đầu bảng xếp hạng", "value": rec.iloc[0]["label"].split(" (")[0],
         "note": f"đạt cả hai kiểm định VaR ở {n_pass}/3 danh mục",
         "pill": (pass_kind, "xếp hạng mô tả")},
        {"label": "ES thấp nhất lúc bình thường", "value": base.xs("Bình thường", level="period").idxmin(),
         "note": f"{100 * base.xs('Bình thường', level='period').min():.2f}% / ngày".replace(".", ","), "accent": ui.T["gold500"]},
        {"label": "Định hướng", "value": "Nghiêng về phía Mỹ", "note": "so với danh mục thuần VN-Index — ngoại lệ: COVID-19",
         "pill": ("info", "không khuyến nghị % cụ thể")},
    ])
    if n_pass == 0:
        st.warning("Không mô hình nào được cả Kupiec và Christoffersen ủng hộ ở VaR 99%. "
                   "Mô hình tự động chỉ là phương án đứng đầu bảng xếp hạng mô tả, không phải mô hình đã đạt backtest.")
    tab1, tab2, tab3 = st.tabs(["Khuyến nghị lựa chọn mô hình", "ES theo tỷ trọng & giới hạn", "Thử tỷ trọng tùy ý"])
    with tab1:
        _recommendation()
        draft = ROOT / "docs" / "application_draft.md"
        if draft.exists():
            with st.expander("Diễn giải đầy đủ (tự sinh từ số liệu)"):
                st.markdown(draft.read_text(encoding="utf-8").split("\n", 1)[1])
    with tab2:
        choices = [AUTO_MODEL, *t14["model"].unique().tolist()]
        selected_model = st.selectbox(
            "Mô hình dùng để đo",
            choices,
            index=0,
            format_func=lambda x: (f"Tự động — {MODEL_LABELS[recommended_model]}" if x == AUTO_MODEL else MODEL_LABELS[x]),
        )
        m = recommended_model if selected_model == AUTO_MODEL else selected_model
        st.caption(f"Đang dùng {MODEL_LABELS[m]}. Tự động chọn theo bảng xếp hạng backtest ở trên.")
        d = t14[t14["model"] == m]
        fig = px.line(d, x="weight", y="ES_mean", color="period", markers=True, category_orders={"weight": ORDER},
                      labels={"weight": "Tỷ trọng VN-Index / S&P 500", "ES_mean": "ES 97,5% trung bình / ngày", "period": ""})
        for L in (0.03, 0.04, 0.05):
            fig.add_hline(y=L, line_dash="dot", line_color=ui.T["muted"], annotation_text=f"giới hạn {int(L * 100)}%", annotation_position="right")
        st.plotly_chart(style(fig, 460, pct=True, title="ES theo tỷ trọng, từng giai đoạn").update_layout(hovermode="closest"), width="stretch")
        st.caption("Mô hình tự động lấy từ đầu bảng khuyến nghị; đường chấm là giới hạn ES minh họa 3/4/5% mỗi ngày.")
        cons = tbl("T14b_allocation_consistency")
        c = cons[(cons["model"] == m) & (cons["limit_L"] == 0.04)]
        st.markdown("**Giới hạn 4%/ngày — thỏa lúc bình thường có còn thỏa khi khủng hoảng?**")
        st.html("<div style='display:flex;gap:10px;flex-wrap:wrap'>" + "".join(
            f"<div class='mr-kpi' style='min-width:150px'><div class='l'>Tỷ trọng {r.weight}</div><div class='n' style='margin-top:6px'>"
            f"{ui.verdict_pill(bool(r.ok_normal), 'Bình thường: thỏa', 'Bình thường: vượt')}<br><br>"
            f"{ui.verdict_pill(bool(r.consistent), 'Khủng hoảng: vẫn thỏa', 'Khủng hoảng: vượt')}</div></div>"
            for r in c.itertuples()) + "</div>")
    with tab3:
        ret = pq("returns.parquet")
        c1, c2, c3 = st.columns([2, 1, 1.8])
        w = c1.slider("Tỷ trọng VN-Index (phần còn lại là S&P 500 quy đổi VND)", 0.0, 1.0, 0.5, 0.05)
        win = c2.select_slider("Cửa sổ (phiên)", [252, 500, 1000], 252)
        model_choice = c3.selectbox(
            "Mô hình dự báo",
            [AUTO_MODEL, *CFG["models_main"]],
            format_func=lambda x: (f"Tự động — {MODEL_LABELS[recommended_model]}" if x == AUTO_MODEL else MODEL_LABELS[x]),
        )
        model = recommended_model if model_choice == AUTO_MODEL else model_choice
        rp = portfolio_return(ret["VN"], ret["SP_VND"], w, 1 - w)
        if len(rp) <= win:
            st.warning(f"Cần nhiều hơn {win} phiên dữ liệu để tính rolling với cửa sổ đã chọn.")
            return
        with st.spinner(f"Đang tính rolling bằng {MODEL_LABELS[model]} — lần đầu có thể mất thời gian..."):
            forecast = _weighted_forecast(rp, model, win, CFG)
        valid = forecast["VaR_99"].notna()
        forecast, realized = forecast.loc[valid], rp.loc[valid]
        var99, es = forecast["VaR_99"], forecast["ES_975"]
        hits = realized < -var99
        ui.kpis([
            {"label": "Phân bổ", "value": f"{w:.0%} VN · {1 - w:.0%} S&P", "note": f"cửa sổ {win} phiên · {MODEL_LABELS[model]}"},
            {"label": "ES 97,5% trung bình", "value": f"{es.mean():.2%}".replace(".", ","), "note": MODEL_LABELS[model]},
            {"label": "Vi phạm VaR 99%", "value": f"{hits.mean():.2%}".replace(".", ","), "note": "kỳ vọng 1%",
             "pill": ("good", "gần kỳ vọng") if abs(hits.mean() - 0.01) < 0.004 else ("warn", "lệch kỳ vọng")},
            {"label": "Dự báo hợp lệ", "value": f"{len(realized):,}".replace(",", "."), "note": "phiên sau khi đủ cửa sổ"},
        ])
        fig = go.Figure()
        fig.add_scatter(x=realized.index, y=realized, name="Lợi suất danh mục", mode="lines", line=dict(color="#9AA6BA", width=0.6))
        fig.add_scatter(x=var99.index, y=-var99, name="−VaR 99%", mode="lines", line=dict(color=ui.SERIES[0], width=1.6))
        fig.add_scatter(x=es.index, y=-es, name="−ES 97,5%", mode="lines", line=dict(color=ui.SERIES[3], width=1.6))
        st.plotly_chart(stress_shapes(style(fig, 400, pct=True, title="Lợi suất và ngưỡng rủi ro của tỷ trọng đã chọn")), width="stretch")
        st.caption("Tự động dùng mô hình đứng đầu bảng khuyến nghị; lần đầu tính tổ hợp này có thể mất thời gian, các lần sau được cache. "
                   "Đây là phân tích minh họa — đề án KHÔNG khuyến nghị tỷ trọng % cụ thể.")
