"""Các trang kết quả theo mục tiêu nghiên cứu MT1 → MT5."""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from dashboard import ui
from dashboard.common import MODEL_LABELS, MODEL_TIER, PORT_LABEL, mt_answers, need_results, periods, pq, stress_shapes, style, tbl
from dashboard.texts import LEVEL_INFO, MODEL_GUIDE_MD, MODEL_INFO, PERIOD_INFO, PORTFOLIO_INFO
from market_risk.backtest.var_tests import christoffersen

MAIN = ["VN100", "VN50_SP50", "SP100"]
ML = lambda m: MODEL_LABELS.get(m, m)  # noqa: E731
SHORT = {"HS": "Lịch sử (HS)", "Normal": "Tham số (Normal)", "MC_Normal": "Monte Carlo", "GARCH_N": "GARCH(1,1)"}  # nhãn trục ngắn


def _answer(key: str, heading: str = "Kết luận chính") -> None:
    a = mt_answers().get(key)
    if a:
        text = "\n".join(line.lstrip("- ").split(" — T")[0] for line in a.splitlines() if line.strip())
        ui.callout(text, heading)


# ---------------------------------------------------------------------------
def page_mt1() -> None:
    ui.page_header("MT1 · Rủi ro danh mục Việt–Mỹ", "VaR, ES 97,5% của 3 danh mục theo bốn phương pháp — dự báo cuốn chiếu 252 phiên", ic="chart")
    if need_results():
        return
    t4 = tbl("T4_var_es_overall")
    d = t4[t4["sample"] == "common"].copy()
    es = d.pivot(index="model", columns="portfolio", values="ES_975")
    red = (1 - es["VN50_SP50"] / es["VN100"]) * 100
    ui.kpis([
        {"label": "ES 97,5% · 100% VN", "value": f"{100 * es['VN100'].median():.2f}%".replace(".", ","), "note": "trung vị bốn phương pháp, mỗi ngày", "accent": ui.SERIES[0]},
        {"label": "ES 97,5% · 50/50", "value": f"{100 * es['VN50_SP50'].median():.2f}%".replace(".", ","), "note": "trung vị bốn phương pháp", "accent": ui.SERIES[1]},
        {"label": "ES 97,5% · 100% S&P", "value": f"{100 * es['SP100'].median():.2f}%".replace(".", ","), "note": "quy đổi VND", "accent": ui.SERIES[2]},
        {"label": "Giảm ES khi 50/50", "value": f"{red.median():.1f}%".replace(".", ","), "note": f"{red.min():.0f}–{red.max():.0f}% tùy mô hình",
         "pill": ("good", f"{int((red > 0).sum())}/4 phương pháp")},
    ])
    _answer("MT1")
    metric = st.segmented_control("Chỉ tiêu", ["ES_975", "VaR_99", "VaR_95"], default="ES_975",
                                  format_func={"ES_975": "ES 97,5% (FRTB)", "VaR_99": "VaR 99%", "VaR_95": "VaR 95%"}.get) or "ES_975"
    d["Danh mục"] = d["portfolio"].map(PORT_LABEL)
    d["Mô hình"] = d["model"].map(lambda m: SHORT.get(m, m))
    order = d[d["portfolio"] == "VN100"].sort_values(metric)["Mô hình"].tolist()
    fig = px.bar(d, x="Mô hình", y=metric, color="Danh mục", barmode="group", category_orders={"Mô hình": order, "Danh mục": [PORT_LABEL[p] for p in MAIN]},
                 color_discrete_map={PORT_LABEL[p]: ui.PORT_COLOR[p] for p in MAIN}, labels={metric: "Mức lỗ trung bình / ngày"})
    fig.update_traces(marker_line_color="#fff", marker_line_width=1.5)
    fig.update_layout(bargap=0.22, hovermode="closest")
    st.plotly_chart(style(fig, 470, pct=True, title=f"{dict(ES_975='ES 97,5%', VaR_99='VaR 99%', VaR_95='VaR 95%')[metric]} trung bình theo mô hình"),
                    width="stretch")
    st.caption("Bốn phương pháp bắt buộc theo đề: Historical Simulation (HS), Parametric (Normal), Monte Carlo (MC_Normal), GARCH(1,1) (GARCH_N).")
    tbl_ = es.copy()
    tbl_.columns = [PORT_LABEL[c] for c in tbl_.columns]
    tbl_["Giảm ES khi 50/50 (%)"] = red.round(1)
    tbl_.insert(0, "Nhóm", [MODEL_TIER.get(m, "") for m in tbl_.index])
    tbl_.insert(0, "Mô hình", [ML(m) for m in tbl_.index])
    ui.table(tbl_.reset_index(drop=True), pct=[PORT_LABEL[p] for p in MAIN])
    t2 = tbl("T2_assumption_tests")
    if t2 is not None:
        with st.expander("Kiểm định giả định — chuẩn, dừng, hiệu ứng ARCH (T2)"):
            _answer("Kiem_dinh_gia_dinh")
            ui.table(t2[["label", "test", "statistic", "p_value", "sig", "conclusion"]], p=["p_value"], num=["statistic"],
                     rename={"label": "Chuỗi", "test": "Kiểm định", "statistic": "Thống kê", "p_value": "p-value",
                             "sig": "Mức ý nghĩa", "conclusion": "Kết luận"})
    with st.expander("Tham số GARCH toàn kỳ — α + β, half-life"):
        t3 = tbl("T3_garch_params")
        ui.table(t3[["series", "model", "alpha", "beta", "persistence", "half_life_days"]],
                 num=["alpha", "beta", "persistence", "half_life_days"],
                 rename={"series": "Chuỗi", "model": "Mô hình", "persistence": "α+β",
                         "half_life_days": "Half-life (phiên)"})


# ---------------------------------------------------------------------------
def _explorer(main: pd.DataFrame) -> None:
    c1, c2, c3, c4 = st.columns([1, 1.6, 0.9, 1.2])
    port = c1.selectbox("Danh mục", MAIN, format_func=PORT_LABEL.get)
    models = c2.multiselect("Phương pháp", sorted(main["model"].unique()), default=sorted(main["model"].unique()),
                            format_func=ML, max_selections=4)
    level = c3.selectbox("Mức", ["VaR_99", "VaR_975", "VaR_95", "ES_975"], format_func=lambda x: LEVEL_INFO[x]["label"])
    pers = periods()
    per = c4.selectbox("Giai đoạn", list(pers))
    if not models:
        st.info("Chọn ít nhất một mô hình.")
        return
    if PERIOD_INFO.get(per) and per != "Toàn kỳ":
        ui.callout(PERIOD_INFO[per].replace("**", ""), "Bối cảnh giai đoạn")
    a, b = pers[per]
    d = main[(main["portfolio"] == port) & main["model"].isin(models)].set_index("Date").sort_index()
    d = d.loc[a:b] if a else d
    if d.empty:
        st.warning("Không có dữ liệu dự báo cho lựa chọn này.")
        return
    fig = go.Figure()
    real = d[d["model"] == models[0]]["realized"]
    fig.add_scatter(x=real.index, y=real, name="Lợi suất thực tế", mode="lines", line=dict(color="#9AA6BA", width=0.8))
    for i, m in enumerate(models):
        g = d[d["model"] == m]
        col = ui.SERIES[i]
        fig.add_scatter(x=g.index, y=-g[level], name=f"−{LEVEL_INFO[level]['label']} · {ML(m)}", mode="lines", line=dict(color=col, width=1.8))
        if level.startswith("VaR"):
            h = g[g[f"exc_{level.split('_')[1]}"] == 1]
            fig.add_scatter(x=h.index, y=h["realized"], mode="markers", name=f"Vi phạm · {ML(m)}",
                            marker=dict(size=8, symbol="x", color=col, line=dict(width=1, color="#fff")))
    st.plotly_chart(stress_shapes(style(fig, 470, pct=True, title=f"{PORT_LABEL[port]} — lợi suất và −{LEVEL_INFO[level]['label']} dự báo")),
                    width="stretch")
    st.caption("Dấu × là ngày lỗ thực tế vượt mức dự báo (vi phạm). Mô hình tốt: đường bám biến động, tỷ lệ vi phạm ≈ mức danh nghĩa.")
    if not level.startswith("VaR"):
        st.info("Kupiec và Christoffersen được áp dụng cho VaR; ES 97,5% được báo cáo như thước đo rủi ro, không có kiểm định ES trong phạm vi hiện tại.")
        return
    lab = level.split("_")[1]
    p = 1 - float("0." + lab)
    rows = []
    for m in models:
        hits = d[d["model"] == m][f"exc_{lab}"].values
        r = christoffersen(hits, p)
        if r["T"] < 2:
            rate = f"{100 * r['rate']:.2f}%" if r["T"] else "—"
            rows.append(f"<tr><td style='padding:10px 12px'><b>{ML(m)}</b></td><td style='padding:10px 12px'>{r['x']}/{r['T']}</td>"
                        f"<td style='padding:10px 12px'>{rate}</td><td style='padding:10px 12px'>—</td>"
                        f"<td style='padding:10px 12px'>—</td><td style='padding:10px 12px'>Không đủ quan sát</td></tr>")
            continue
        ok = r["p_uc"] >= 0.05 and r["p_cc"] >= 0.05
        if ok:
            verdict = ui.pill("good", "Đạt")
        elif r["p_uc"] < 0.05:
            verdict = ui.pill("bad", "Đánh giá THẤP rủi ro") if r["rate"] > p else ui.pill("warn", "Quá thận trọng")
        else:
            verdict = ui.pill("warn", "Tần suất đạt, vi phạm dồn cụm")
        rows.append(f"<tr><td style='padding:10px 12px'><b>{ML(m)}</b></td><td style='padding:10px 12px'>{r['x']}/{r['T']}</td>"
                    f"<td style='padding:10px 12px'>{ui.num(100 * r['rate'], 2, '%')} <span style='color:{ui.T['muted']}'>(kỳ vọng {ui.num(100 * p, 1, '%')})</span></td>"
                    f"<td style='padding:10px 12px'>{ui.num(r['p_uc'], 3)}</td><td style='padding:10px 12px'>{ui.num(r['p_cc'], 3)}</td><td style='padding:10px 12px'>{verdict}</td></tr>")
    st.html(f"<div class='mr-card' style='padding:4px 6px'><table style='width:100%;border-collapse:collapse;font-size:14px'><thead>"
            f"<tr style='text-align:left;color:{ui.T['muted']};font-size:12px;text-transform:uppercase;letter-spacing:.06em'>"
            "<th style='padding:10px 12px'>Mô hình</th><th style='padding:10px 12px'>Vi phạm</th><th style='padding:10px 12px'>Tỷ lệ</th>"
            "<th style='padding:10px 12px'>p Kupiec</th><th style='padding:10px 12px'>p Christoffersen</th><th style='padding:10px 12px'>Kết luận</th>"
            f"</tr></thead><tbody>{''.join(rows)}</tbody></table></div>")
    st.caption("Đạt khi p Kupiec và p Christoffersen đều ≥ 0,05 (không bác bỏ mô hình ở mức 5%).")
    with st.expander("Mỗi mô hình đo lường điều gì?"):
        st.markdown(MODEL_GUIDE_MD)
        for m in models:
            st.markdown(MODEL_INFO.get(m, ""))
    st.caption(PORTFOLIO_INFO.get(port, {}).get("desc", ""))


def page_backtest() -> None:
    ui.page_header("MT4 · Kiểm định ngược (backtest)", "Kupiec kiểm tra tần suất vi phạm; Christoffersen kiểm tra độc lập và bao phủ có điều kiện", ic="check")
    if need_results():
        return
    pt = tbl("T5b_pass_table")
    passes = pt[pt["pass_all"]].groupby("model").size().sort_values(ascending=False)
    t5m = tbl("T5_backtest_var")
    worst = t5m[(t5m["set"] == "main") & (t5m["level"] == 0.99)].groupby("model")["rate"].mean().sort_values(ascending=False)
    ui.kpis([
        {"label": "Không bị bác bỏ bởi cả hai · VaR99", "value": ", ".join(ML(m).split(" (")[0] for m in passes.index) or "—",
         "note": " · ".join(f"{ML(m).split(' (')[0]} {n}/3" for m, n in passes.items()) or "cửa sổ 252 phiên, 3 danh mục chính",
         "pill": ("good", "dùng để kết luận") if len(passes) else ("warn", "không mô hình nào đạt"),
         "accent": ui.T["good"] if len(passes) else ui.T["warn"]},
        {"label": "Mô hình trượt nặng nhất", "value": ML(worst.index[0]).split(" (")[0],
         "note": f"vi phạm VaR99 trung bình {ui.num(100 * worst.iloc[0], 2, '%')} (kỳ vọng 1%)", "pill": ("bad", "không dùng ở 99%"), "accent": ui.T["bad"]},
    ])
    tab1, tab2 = st.tabs(["Khám phá từng mô hình", "Bảng tổng hợp kiểm định"])
    with tab1:
        fc = pq("rolling_forecasts.parquet")
        _explorer(fc[fc["set"] == "main"])
    with tab2:
        m = pt.pivot(index="model", columns="portfolio", values="pass_all").reindex(columns=MAIN)
        order = m.sum(axis=1).sort_values(ascending=False).index
        rows = "".join(f"<tr><td style='padding:9px 12px'><b>{ML(i)}</b> <span style='color:{ui.T['muted']}'>{MODEL_TIER.get(i, '')}</span></td>"
                       + "".join(f"<td style='padding:9px 12px'>{ui.verdict_pill(bool(m.loc[i, c]))}</td>" for c in MAIN) + "</tr>" for i in order)
        st.html(f"<div class='mr-card' style='padding:4px 6px'><table style='width:100%;border-collapse:collapse;font-size:14px'><thead>"
                f"<tr style='text-align:left;color:{ui.T['muted']};font-size:12px;text-transform:uppercase;letter-spacing:.06em'>"
                f"<th style='padding:9px 12px'>Mô hình — không bị bác bỏ bởi cả hai?</th>" + "".join(f"<th style='padding:9px 12px'>{PORT_LABEL[c]}</th>" for c in MAIN)
                + f"</tr></thead><tbody>{rows}</tbody></table></div>")
        t5 = tbl("T5_backtest_var")
        ui.section("VaR 99% — Kupiec và Christoffersen", "check")
        v = t5[(t5["set"] == "main") & (t5["level"] == 0.99)].copy()
        v["model"] = v["model"].map(ML)
        v["portfolio"] = v["portfolio"].map(PORT_LABEL)
        ui.table(v[["portfolio", "model", "T", "x", "expected", "rate", "p_uc", "p_ind", "p_cc", "conclusion"]],
                 pct=["rate"], p=["p_uc", "p_ind", "p_cc"],
                 rename={"portfolio": "Danh mục", "model": "Mô hình", "T": "Số ngày", "x": "Vi phạm", "rate": "Tỷ lệ",
                         "expected": "Vi phạm kỳ vọng", "p_uc": "p Kupiec", "p_ind": "p độc lập", "p_cc": "p Christoffersen",
                         "conclusion": "Kết luận"}, height=420)


# ---------------------------------------------------------------------------
def page_mt2() -> None:
    ui.page_header("MT2 · Lợi ích đa dạng hóa theo thời gian", "Khi tương quan VN–Mỹ tăng, lợi ích giảm rủi ro có suy yếu không?", ic="layers")
    if need_results():
        return
    t8 = tbl("T8_diversification_by_corr")
    d = t8[(t8["model"] == "GARCH_N") & (t8["metric"] == "DR") & (t8["corr_measure"] == "corr_252")].set_index("tercile")
    ui.kpis([
        {"label": "Lợi ích khi tương quan thấp", "value": f"{100 * d.loc['Thấp', 'mean']:.1f}%".replace(".", ","), "note": "giảm ES tương đối (DR)", "accent": ui.SERIES[2]},
        {"label": "Lợi ích khi tương quan cao", "value": f"{100 * d.loc['Cao', 'mean']:.1f}%".replace(".", ","), "note": "vẫn dương — không biến mất", "accent": ui.SERIES[3]},
        {"label": "Chênh lệch", "value": f"{100 * d.loc['Cao − Thấp', 'mean']:.1f} điểm %".replace(".", ","),
         "note": f"block bootstrap p = {d.loc['Cao − Thấp', 'p_block_bootstrap']:.3f}", "pill": ("info", "mô tả, không nhân quả")},
    ])
    _answer("MT2")
    c = pq("correlations.parquet")
    cols = {"corr_252": "Trượt 252 phiên", "corr_dcc": "DCC-GARCH", "corr_lag_252": "Trượt 252, S&P lệch pha t−1", "corr_63": "Trượt 63 phiên", "corr_ewma": "EWMA"}
    pick = st.multiselect("Thước đo tương quan", list(cols), default=["corr_252", "corr_dcc", "corr_lag_252"], format_func=cols.get, max_selections=4)
    fig = go.Figure()
    for i, k in enumerate(pick):
        fig.add_scatter(x=c.index, y=c[k], name=cols[k], mode="lines", line=dict(color=ui.SERIES[i], width=1.6))
    fig.add_hline(y=0, line_color=ui.T["border"])
    st.plotly_chart(stress_shapes(style(fig, 380, title="Tương quan VN-Index – S&P 500 (VND) theo thời gian")), width="stretch")
    dv = pq("diversification_timeseries.parquet")
    x = dv[dv["model"] == "GARCH_N"]
    fig = go.Figure(go.Scatter(x=x.index, y=x["DR"], name="DR — giảm ES tương đối", mode="lines", line=dict(color=ui.SERIES[2], width=1.2)))
    st.plotly_chart(stress_shapes(style(fig, 330, pct=True, title="Lợi ích đa dạng hóa DR theo thời gian (ES GARCH_N)")), width="stretch")
    st.caption("DR = 1 − ES(50/50) / [0,5·ES(100% VN) + 0,5·ES(100% S&P)]. DR càng cao, thêm S&P càng giảm rủi ro đuôi.")
    with st.expander("Bảng chi tiết — theo tam phân vị tương quan, tương quan đuôi, Forbes–Rigobon"):
        ui.table(t8[t8["model"] == "GARCH_N"][["corr_measure", "metric", "tercile", "N", "mean", "p_block_bootstrap"]],
                 pct=["mean"], p=["p_block_bootstrap"], rename={"corr_measure": "Thước đo", "metric": "Chỉ tiêu", "tercile": "Tam phân vị",
                                                                 "mean": "Trung bình", "p_block_bootstrap": "p block bootstrap"})
        ui.table(tbl("T8b_tail_correlation"), num=["corr_emp", "corr_normal_implied", "excess", "corr_uncond"],
                 rename={"q": "Ngưỡng", "side": "Chiều", "corr_emp": "Tương quan thực tế", "n_obs": "Số ngày",
                         "corr_normal_implied": "Nếu Normal", "excess": "Chênh", "corr_uncond": "Tương quan chung"})
        ui.table(tbl("T8d_forbes_rigobon"), num=["corr_calm", "corr_stress", "delta_var", "corr_adjusted_FR"],
                 rename={"data": "Dữ liệu", "period": "Giai đoạn", "corr_calm": "Yên ổn", "corr_stress": "Stress",
                         "corr_adjusted_FR": "Sau hiệu chỉnh F–R"})


# ---------------------------------------------------------------------------
def page_mt3() -> None:
    ui.page_header("MT3 · Tỷ giá & bối cảnh lạm phát", "Lợi ích S&P còn giữ được sau quy đổi VND không? Rủi ro khác nhau thế nào giữa lạm phát thấp/cao?", ic="db")
    if need_results():
        return
    t9, t10 = tbl("T9_fx_effect"), tbl("T10_inflation_regimes")
    f = t9[(t9["period"] == "Toàn kỳ") & (t9["portfolio"] == "100% S&P")]["dES_FX"] * 100
    inf = t10[(t10["split"] == "ngưỡng 4%")].set_index("metric")
    ui.kpis([
        {"label": "ES tăng do quy đổi VND", "value": f"{f.min():+.2f} → {f.max():+.2f} đ.%".replace(".", ","), "note": "100% S&P, toàn kỳ, theo mô hình",
         "pill": ("good", "gần như 0")},
        {"label": "ES 100% VN · lạm phát cao", "value": f"{100 * inf.loc['ES_VN', 'mean_Cao']:.2f}%".replace(".", ","), "note": "khi lạm phát > 4%", "accent": ui.SERIES[3]},
        {"label": "ES 100% VN · lạm phát thấp", "value": f"{100 * inf.loc['ES_VN', 'mean_Thap']:.2f}%".replace(".", ","),
         "note": f"p = {inf.loc['ES_VN', 'p_block_bootstrap']:.3f}", "accent": ui.SERIES[0], "pill": ("info", "so sánh bối cảnh")},
    ])
    _answer("MT3")
    per = st.selectbox("Giai đoạn", t9["period"].unique().tolist())
    d = t9[t9["period"] == per].melt(id_vars=["portfolio", "model"], value_vars=["ES_VND", "ES_USD"])
    d["variable"] = d["variable"].map({"ES_VND": "Tính bằng VND", "ES_USD": "Tính bằng USD (phòng ngừa tỷ giá)"})
    fig = px.bar(d, x="model", y="value", color="variable", facet_col="portfolio", barmode="group",
                 color_discrete_sequence=[ui.SERIES[0], ui.SERIES[1]], labels={"value": "ES 97,5%", "model": "", "variable": ""})
    fig.for_each_annotation(lambda a: a.update(text=a.text.split("=")[-1]))
    st.plotly_chart(style(fig, 380, pct=True, title="ES bằng VND so với bằng USD").update_layout(hovermode="closest"), width="stretch")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        ce = tbl("T9b_component_es")
        fig = px.bar(ce[ce["w_VN"] == 0.5], x="period", y="CES", color="component", color_discrete_sequence=ui.SERIES[:3],
                     labels={"CES": "Đóng góp vào ES", "period": "", "component": ""})
        fig.update_traces(marker_line_color="#fff", marker_line_width=1.5)
        st.plotly_chart(style(fig, 360, pct=True, title="Component ES (Euler) — danh mục 50/50").update_layout(hovermode="closest"), width="stretch")
    with c2:
        st.markdown("**Theo chế độ lạm phát** (ngưỡng 4%)")
        ui.table(inf.reset_index()[["metric", "mean_Thap", "mean_Cao", "p_block_bootstrap"]], num=["mean_Thap", "mean_Cao"], p=["p_block_bootstrap"],
                 rename={"metric": "Chỉ tiêu", "mean_Thap": "Lạm phát thấp", "mean_Cao": "Lạm phát cao", "p_block_bootstrap": "p"})
    with st.expander("Mô hình VAR (Bài 9) — S&P 500, tỷ giá → VN-Index"):
        _answer("VAR_lan_toa", "Kết quả VAR")
        ui.table(tbl("T16_var_granger"), num=["F"], p=["p_value"], rename={"cause": "Nguyên nhân (Granger)", "effect": "Kết quả", "p_value": "p",
                                                                             "conclusion": "Kết luận"})
    with st.expander("Độ nhạy với nguồn/cách làm sạch tỷ giá · lợi suất thực"):
        ui.table(tbl("T9c_clean_sample_robustness"), pct=["vol_FX_ann", "ES_VN100", "ES_5050", "ES_SP100", "ES_SP_USD", "DR_static"],
                 rename={"variant": "Biến thể", "vol_FX_ann": "Biến động tỷ giá/năm", "DR_static": "DR"})
        ui.table(tbl("T10b_real_returns"), pct=["nominal_ann", "inflation_ann", "real_ann", "real_vol_ann"],
                 rename={"portfolio": "Danh mục", "nominal_ann": "Danh nghĩa/năm", "inflation_ann": "Lạm phát/năm", "real_ann": "Thực/năm"})


# ---------------------------------------------------------------------------
def page_mt5() -> None:
    ui.page_header("MT5 · Stress test", "2008 · 2011–12 · 2018 · 2020 · 2022 — mô hình nào đánh giá thiếu rủi ro khi khủng hoảng?", ic="alert")
    if need_results():
        return
    t11 = tbl("T11_stress_historical")
    core = t11[t11["period"].isin(["GFC_2008", "TradeWar_2018", "COVID_2020", "Tightening_2022"])]
    u = core.groupby("model")["UR_VaR99"].mean()
    ui.kpis([
        {"label": "Đánh giá thiếu nhất", "value": ML(u.idxmax()).split(" (")[0], "note": f"vi phạm VaR99 gấp {ui.num(u.max(), 1)}× kỳ vọng", "accent": ui.T["bad"],
         "pill": ("bad", "không dùng khi khủng hoảng")},
        {"label": "Sát kỳ vọng nhất", "value": ML(u.idxmin()).split(" (")[0], "note": f"vi phạm VaR99 gấp {ui.num(u.min(), 1)}× kỳ vọng",
         "accent": ui.T["good"] if u.min() < 2 else ui.T["warn"],
         "pill": ("good", "đáng tin") if u.min() < 2 else ("warn", "tốt nhất nhưng vẫn vượt kỳ vọng")},
        {"label": "Sụt giảm tối đa GFC", "value": f"{100 * t11[t11['period'] == 'GFC_2008'].groupby('portfolio')['max_drawdown'].first()['VN100']:.0f}%",
         "note": "100% VN-Index, 2008–2009"},
    ])
    _answer("MT5")
    labels = dict(zip(t11["period"], t11["label"]))
    per = st.segmented_control("Giai đoạn", list(labels), default="COVID_2020", format_func=labels.get) or "COVID_2020"
    d = t11[t11["period"] == per].copy()
    d["Mô hình"] = d["model"].map(lambda m: ML(m).split(" (")[0])
    d["Danh mục"] = d["portfolio"].map(PORT_LABEL)
    fig = px.bar(d, x="Mô hình", y="UR_VaR99", color="Danh mục", barmode="group",
                 color_discrete_map={PORT_LABEL[p]: ui.PORT_COLOR[p] for p in MAIN}, labels={"UR_VaR99": "Vi phạm thực tế / kỳ vọng"})
    fig.add_hline(y=1, line_dash="dash", line_color=ui.T["navy800"], annotation_text="= kỳ vọng")
    fig.update_traces(marker_line_color="#fff", marker_line_width=1.5)
    st.plotly_chart(style(fig, 420, title=f"{labels[per]} — số lần vi phạm VaR99 so với kỳ vọng").update_layout(hovermode="closest"),
                    width="stretch")
    st.caption("Cột càng cao → mô hình càng đánh giá THIẾU rủi ro trong giai đoạn này.")
    ui.section("Máy tính kịch bản giả định", "alert", "tự nhập cú sốc — tái định giá đầy đủ")
    c1, c2, c3, c4 = st.columns(4)
    notional = c1.number_input("Giá trị danh mục (tỷ VND)", 0.1, 1000.0, 1.0, 0.1)
    vn = c2.slider("Cú sốc VN-Index (%)", -20.0, 10.0, -7.0, 0.5) / 100
    sp = c3.slider("Cú sốc S&P 500 (%)", -20.0, 10.0, -10.0, 0.5) / 100
    fx = c4.slider("USD/VND thay đổi (%)", -10.0, 10.0, 0.0, 0.5) / 100
    res = pd.DataFrame([{"Tỷ trọng VN/S&P": f"{int(w * 100)}/{int(100 - w * 100)}",
                         "Lãi/lỗ (%)": w * vn + (1 - w) * ((1 + sp) * (1 + fx) - 1)} for w in (1.0, 0.75, 0.5, 0.25, 0.0)])
    res["Lãi/lỗ (triệu VND)"] = res["Lãi/lỗ (%)"] * notional * 1000
    fig = px.bar(res, x="Tỷ trọng VN/S&P", y="Lãi/lỗ (%)", text=res["Lãi/lỗ (triệu VND)"].map(lambda v: f"{v:,.1f} tr"))
    fig.update_traces(marker_color=[ui.T["bad"] if v < 0 else ui.T["good"] for v in res["Lãi/lỗ (%)"]], textposition="outside")
    st.plotly_chart(style(fig, 330, pct=True, title="Lãi/lỗ của danh mục theo tỷ trọng").update_layout(hovermode="closest"), width="stretch")
    with st.expander("Bảng chi tiết stress test lịch sử"):
        ui.table(d[["Danh mục", "Mô hình", "N", "mean_ES975", "worst_loss", "max_drawdown", "exc99", "UR_VaR99", "UR_ES", "reaction_lag_days"]],
                 pct=["mean_ES975", "worst_loss", "max_drawdown"], num=["UR_VaR99", "UR_ES"],
                 rename={"N": "Số ngày", "mean_ES975": "ES TB", "worst_loss": "Lỗ tệ nhất", "max_drawdown": "Sụt giảm tối đa", "exc99": "Vi phạm VaR99",
                         "UR_VaR99": "Vi phạm/kỳ vọng", "UR_ES": "Lỗ thực/ES", "reaction_lag_days": "Độ trễ phản ứng (phiên)"})
