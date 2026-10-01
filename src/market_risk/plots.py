"""Phase 10 — Trực quan hóa (PNG + PDF, 300 dpi, nhãn tiếng Việt, bảng màu Okabe–Ito thân thiện người mù màu).

Mọi biểu đồ chuỗi thời gian tô xám các giai đoạn stress; góc dưới phải ghi nguồn dữ liệu.
"""

from __future__ import annotations

import logging

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from scipy import stats  # noqa: E402
from statsmodels.graphics.tsaplots import plot_acf  # noqa: E402
from statsmodels.nonparametric.smoothers_lowess import lowess  # noqa: E402

from .config import enabled_periods, load_config, path_of, read_table  # noqa: E402
from .models import MODEL_LABELS  # noqa: E402

log = logging.getLogger(__name__)
OKABE = ["#0072B2", "#E69F00", "#009E73", "#D55E00", "#CC79A7", "#56B4E9", "#F0E442", "#000000"]
SOURCE = "Nguồn dữ liệu: Investing.com (giá ngày), IMF IFS (CPI); tính toán của nhóm"
PORT = {"VN100": "100% VN-Index", "VN50_SP50": "50/50", "SP100": "100% S&P 500 (VND)"}
KEY_MODELS = ["HS", "Normal", "MC_Normal", "GARCH_N"]

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.titlesize": 10, "axes.grid": True,
                     "grid.alpha": 0.3, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.prop_cycle": matplotlib.cycler(color=OKABE), "figure.dpi": 100, "savefig.dpi": 300,
                     "legend.frameon": False})


def shade(ax, cfg: dict, label: bool = False) -> None:
    """Tô xám các giai đoạn stress."""
    for i, p in enumerate(enabled_periods(cfg).values()):
        ax.axvspan(pd.Timestamp(p["start"]), pd.Timestamp(p["end"]), color="grey", alpha=0.18, lw=0,
                   label="Giai đoạn stress" if (label and i == 0) else None)


def save(fig, name: str, cfg: dict) -> None:
    fig.text(0.99, -0.01, SOURCE, ha="right", va="top", fontsize=6, color="grey")
    out = path_of("figures", cfg)
    fig.savefig(out / f"{name}.png", bbox_inches="tight")
    fig.savefig(out / f"{name}.pdf", bbox_inches="tight")
    plt.close(fig)
    log.info("Đã lưu hình %s", name)


def pct(ax, axis: str = "y") -> None:
    fmt = matplotlib.ticker.PercentFormatter(1.0, decimals=0 if axis == "y" else 1)
    (ax.yaxis if axis == "y" else ax.xaxis).set_major_formatter(fmt)


# ---------------------------------------------------------------------------
def f1_prices(prices: pd.DataFrame, cfg: dict) -> None:
    fig, ax = plt.subplots(figsize=(9, 4))
    norm = pd.DataFrame({"VN-Index": prices["VN"], "S&P 500 (USD)": prices["SP_USD"],
                         "S&P 500 quy đổi VND": prices["SP_USD"] * prices["USDVND"]})
    (100 * norm / norm.iloc[0]).plot(ax=ax, lw=1)
    shade(ax, cfg, True)
    ax.set_yscale("log")
    ax.set(title="F1. Giá chuẩn hóa (ngày đầu = 100, thang log)", xlabel="", ylabel="Chỉ số (log)")
    ax.legend(loc="upper left")
    save(fig, "F1_normalized_prices", cfg)


def f2_returns(r: pd.DataFrame, cfg: dict) -> None:
    fig, axes = plt.subplots(3, 1, figsize=(9, 6.5), sharex=True)
    for ax, (c, lab) in zip(axes, [("VN", "VN-Index"), ("SP_VND", "S&P 500 (VND)"), ("USDVND", "USD/VND")]):
        ax.plot(r.index, r[c], lw=0.4, color=OKABE[0])
        shade(ax, cfg)
        ax.set_title(f"Lợi suất log ngày — {lab}", loc="left")
        pct(ax)
    fig.suptitle("F2. Lợi suất theo thời gian: biến động theo cụm", x=0.01, ha="left")
    save(fig, "F2_returns", cfg)


def f3_f4_distribution(r: pd.DataFrame, cfg: dict) -> None:
    cols = [("VN", "VN-Index"), ("SP_VND", "S&P 500 (VND)"), ("VN50_SP50", "Danh mục 50/50")]
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4))
    for ax, (c, lab) in zip(axes, cols):
        x = r[c].values
        ax.hist(x, bins=120, density=True, alpha=0.5, color=OKABE[5])
        g = np.linspace(np.quantile(x, 0.0005), np.quantile(x, 0.9995), 400)
        ax.plot(g, stats.norm.pdf(g, x.mean(), x.std()), label="Normal", color=OKABE[3])
        ax.set_title(lab)
        pct(ax, "x")
        ax.legend(fontsize=7)
    fig.suptitle("F3. Phân phối lợi suất và mật độ Normal tham chiếu", x=0.01, ha="left")
    save(fig, "F3_histogram", cfg)
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4))
    for ax, (c, lab) in zip(axes, cols):
        z = (r[c] - r[c].mean()) / r[c].std()
        (osm, osr), (sl, ic, _) = stats.probplot(z, dist="norm")
        ax.scatter(osm, osr, s=3, color=OKABE[0])
        ax.plot(osm, sl * osm + ic, color=OKABE[3], lw=1)
        ax.set(title=lab, xlabel="Phân vị Normal lý thuyết", ylabel="Phân vị mẫu (chuẩn hóa)")
    fig.suptitle("F4. QQ-plot so với Normal: lệch mạnh ở hai đuôi", x=0.01, ha="left")
    save(fig, "F4_qqplot", cfg)


def f5_acf(r: pd.DataFrame, cfg: dict) -> None:
    fig, axes = plt.subplots(2, 2, figsize=(10, 5.5))
    for j, (c, lab) in enumerate([("VN", "VN-Index"), ("SP_VND", "S&P 500 (VND)")]):
        plot_acf(r[c], lags=30, ax=axes[0, j], zero=False, title=f"ACF lợi suất — {lab}")
        plot_acf(r[c] ** 2, lags=30, ax=axes[1, j], zero=False, title=f"ACF bình phương lợi suất — {lab}")
    fig.suptitle("F5. Tự tương quan của r và r²: r² tự tương quan mạnh → hiệu ứng ARCH", x=0.01, ha="left")
    fig.tight_layout()
    save(fig, "F5_acf", cfg)


def f6_inflation(cfg: dict) -> None:
    m = pd.read_csv(path_of("processed", cfg) / "cpi_inflation.csv", index_col=0, parse_dates=True, encoding="utf-8-sig")
    fig, ax = plt.subplots(figsize=(9, 3.6))
    ax.plot(m.index, m["inflation_yoy"], color=OKABE[3], lw=1.2, label="Lạm phát so cùng kỳ (tính từ CPI)")
    hi = m["regime"] == "Cao"
    ax.fill_between(m.index, 0, m["inflation_yoy"].max() * 1.05, where=hi, color=OKABE[1], alpha=0.2, step="mid",
                    label="Chế độ lạm phát cao")
    ax.axhline(cfg["inflation"]["threshold"], ls="--", color="black", lw=0.8,
               label=f"Ngưỡng {cfg['inflation']['threshold']:.0%}")
    ax.set(title="F6. Lạm phát Việt Nam (YoY) và chế độ lạm phát", ylabel="")
    pct(ax)
    ax.legend(loc="upper right")
    save(fig, "F6_inflation_regime", cfg)


def f7_var_paths(fc: pd.DataFrame, cfg: dict) -> None:
    for port, lab in PORT.items():
        fig, ax = plt.subplots(figsize=(10, 4))
        g = fc[fc["portfolio"] == port]
        base = g[g["model"] == "HS"].set_index("Date")
        ax.plot(base.index, base["realized"], lw=0.35, color="grey", label="Lợi suất thực tế")
        for i, m in enumerate(KEY_MODELS):
            s = g[g["model"] == m].set_index("Date")
            ax.plot(s.index, -s["VaR_99"], lw=0.7, color=OKABE[i], label=f"−VaR99 {MODEL_LABELS[m]}")
        exc = g[(g["model"] == "GARCH_N") & (g["exc_99"] == 1)]
        ax.scatter(exc["Date"], exc["realized"], s=8, color=OKABE[3], zorder=5, label="Vi phạm (GARCH_N)")
        shade(ax, cfg)
        pct(ax)
        ax.set(title=f"F7. Lợi suất và −VaR 99% dự báo — {lab}")
        ax.legend(ncol=3, fontsize=7, loc="lower left")
        save(fig, f"F7_var_paths_{port}", cfg)


def f8_crisis_zoom(fc: pd.DataFrame, cfg: dict, port: str = "VN50_SP50") -> None:
    per = {k: v for k, v in enabled_periods(cfg).items() if k in cfg["core_stress"]}
    fig, axes = plt.subplots(2, 2, figsize=(11, 6.5))
    g = fc[fc["portfolio"] == port]
    for ax, p in zip(axes.flat, per.values()):
        a, b = pd.Timestamp(p["start"]) - pd.Timedelta(days=30), pd.Timestamp(p["end"]) + pd.Timedelta(days=30)
        base = g[g["model"] == "HS"].set_index("Date").loc[a:b]
        ax.bar(base.index, base["realized"], color="grey", width=1.0, label="Lợi suất")
        for i, m in enumerate(KEY_MODELS):
            s = g[g["model"] == m].set_index("Date").loc[a:b]
            ax.plot(s.index, -s["VaR_99"], lw=1, color=OKABE[i], label=MODEL_LABELS[m])
        ax.axvspan(pd.Timestamp(p["start"]), pd.Timestamp(p["end"]), color="grey", alpha=0.12)
        ax.set_title(p["label"], fontsize=9)
        pct(ax)
        ax.tick_params(axis="x", labelsize=7, rotation=30)
    axes[0, 0].legend(fontsize=7)
    fig.suptitle(f"F8. Phóng to các khủng hoảng — −VaR 99%, danh mục {PORT[port]}", x=0.01, ha="left")
    fig.tight_layout()
    save(fig, "F8_crisis_zoom", cfg)


def f9_exceed_counts(t5: pd.DataFrame, cfg: dict) -> None:
    d = t5[(t5["set"] == "main") & (t5["level"] == 0.99)]
    fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharey=True)
    for ax, (port, lab) in zip(axes, PORT.items()):
        s = d[d["portfolio"] == port].set_index("model").sort_values("rate")
        colors = [OKABE[2] if p >= 0.05 else OKABE[3] for p in s["p_uc"]]
        ax.barh(s.index, 100 * s["rate"], color=colors)
        ax.axvline(1.0, ls="--", color="black", lw=0.8)
        ax.set(title=lab, xlabel="Tỷ lệ vi phạm VaR 99% (%)")
    fig.suptitle("F9. Tỷ lệ vi phạm VaR 99% (đường đứt = 1% kỳ vọng; xanh = Kupiec không bác bỏ, cam = bác bỏ)",
                 x=0.01, ha="left")
    fig.tight_layout()
    save(fig, "F9_exceedances", cfg)


def f10_corr(cfg: dict) -> None:
    c = pd.read_parquet(path_of("processed", cfg) / "correlations.parquet")
    fig, ax = plt.subplots(figsize=(10, 4))
    for i, (col, lab) in enumerate([("corr_252", "Trượt 252 phiên"), ("corr_63", "Trượt 63 phiên"),
                                    ("corr_ewma", "EWMA λ=0,94"), ("corr_dcc", "DCC-GARCH(1,1)"),
                                    ("corr_lag_252", "Trượt 252, S&P lệch pha t−1")]):
        ax.plot(c.index, c[col], lw=1.1 if col in ("corr_252", "corr_lag_252") else 0.5, color=OKABE[i], label=lab)
    shade(ax, cfg, True)
    ax.axhline(0, color="black", lw=0.5)
    ax.set(title="F10. Tương quan VN-Index – S&P 500 (VND) theo thời gian", ylabel="Hệ số tương quan")
    ax.legend(ncol=3, fontsize=7)
    save(fig, "F10_rolling_corr", cfg)


def f11_div(cfg: dict) -> None:
    d = pd.read_parquet(path_of("processed", cfg) / "diversification_timeseries.parquet")
    d = d[d["model"] == cfg["diversification"]["primary_model"]]
    fig, axes = plt.subplots(2, 1, figsize=(10, 5.5), sharex=True)
    axes[0].plot(d.index, d["DB"], lw=0.6, color=OKABE[0])
    axes[0].set_title("DB_t = ES(100% VN) − ES(50/50): mức giảm ES khi thêm S&P", loc="left")
    axes[1].plot(d.index, d["DR"], lw=0.6, color=OKABE[2])
    axes[1].set_title("DR_t = 1 − ES(50/50) / [0,5·ES(VN) + 0,5·ES(S&P)]: lợi ích tương đối", loc="left")
    for ax in axes:
        shade(ax, cfg)
        pct(ax)
    fig.suptitle(f"F11. Lợi ích đa dạng hóa theo thời gian ({MODEL_LABELS[cfg['diversification']['primary_model']]})",
                 x=0.01, ha="left")
    save(fig, "F11_div_benefit", cfg)
    fig, ax = plt.subplots(figsize=(6, 4.5))
    x = d[["corr_252", "DR"]].dropna()
    ax.scatter(x["corr_252"], x["DR"], s=2, alpha=0.3, color=OKABE[0])
    lw = lowess(x["DR"], x["corr_252"], frac=0.3)
    ax.plot(lw[:, 0], lw[:, 1], color=OKABE[3], lw=2, label="LOWESS")
    pct(ax)
    ax.set(title="F11b. DR_t theo tương quan trượt 252 phiên", xlabel="Tương quan VN–S&P (252 phiên)", ylabel="DR_t")
    ax.legend()
    save(fig, "F11b_scatter_dr_corr", cfg)


def f12_es_weight(t14: pd.DataFrame, cfg: dict) -> None:
    order = ["100/0", "75/25", "50/50", "25/75", "0/100"]
    for m in t14["model"].unique():
        d = t14[t14["model"] == m].pivot(index="weight", columns="period", values="ES_mean").reindex(order) * 100
        fig, ax = plt.subplots(figsize=(8, 4.2))
        for i, col in enumerate(d.columns):
            ax.plot(order, d[col], marker="o", lw=2.2 if col in ("Toàn kỳ", "Bình thường") else 1,
                    ls="-" if col in ("Toàn kỳ", "Bình thường") else "--", color=OKABE[i % 8], label=col)
        for L in cfg["application"]["es_limits"]:
            ax.axhline(100 * L, color="grey", lw=0.6, ls=":")
        ax.set(title=f"F12. ES 97,5% trung bình theo tỷ trọng VN/S&P — {MODEL_LABELS[m]}",
               xlabel="Tỷ trọng VN-Index / S&P 500", ylabel="ES 97,5% (%/ngày)")
        ax.legend(fontsize=7, ncol=2)
        save(fig, f"F12_es_by_weight_{m}", cfg)


def f13_garch_vol(fc: pd.DataFrame, cfg: dict) -> None:
    fig, ax = plt.subplots(figsize=(10, 4))
    for i, (p, lab) in enumerate(PORT.items()):
        s = fc[(fc["portfolio"] == p) & (fc["model"] == "GARCH_N")].set_index("Date")["sigma"] * np.sqrt(252)
        ax.plot(s.index, s, lw=0.7, color=OKABE[i], label=lab)
    shade(ax, cfg, True)
    pct(ax)
    ax.set(title="F13. Biến động có điều kiện GARCH(1,1)-Normal (năm hóa, dự báo 1 ngày)")
    ax.legend()
    save(fig, "F13_garch_vol", cfg)


def f14_heatmap(t5: pd.DataFrame, cfg: dict) -> None:
    d = t5[(t5["set"] == "main")]
    fig, axes = plt.subplots(1, 3, figsize=(13, 5), sharey=True)
    for ax, (port, lab) in zip(axes, PORT.items()):
        s = d[d["portfolio"] == port]
        tab = pd.DataFrame({
            "Kupiec 99": s[s["level"] == 0.99].set_index("model")["p_uc"],
            "Chr. ind 99": s[s["level"] == 0.99].set_index("model")["p_ind"],
            "Chr. cc 99": s[s["level"] == 0.99].set_index("model")["p_cc"],
        })
        im = ax.imshow(tab.values.astype(float), cmap="viridis", vmin=0, vmax=0.2, aspect="auto")
        ax.set_xticks(range(tab.shape[1]), tab.columns, rotation=45, ha="right", fontsize=7)
        ax.set_yticks(range(tab.shape[0]), tab.index, fontsize=7)
        for (i, j), v in np.ndenumerate(tab.values.astype(float)):
            if np.isfinite(v):
                ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=5.5, color="white" if v < 0.1 else "black")
        ax.set_title(lab)
        ax.grid(False)
    fig.colorbar(im, ax=axes, shrink=0.7, label="p-value (≥ 0,05 = không bác bỏ)")
    fig.suptitle("F14. p-value Kupiec và Christoffersen (tối = bác bỏ)", x=0.01, ha="left")
    save(fig, "F14_backtest_heatmap", cfg)


def f16_inflation_es(cfg: dict) -> None:
    d = pd.read_parquet(path_of("processed", cfg) / "regime_frame.parquet").dropna(subset=["regime"])
    fig, axes = plt.subplots(1, 4, figsize=(12, 3.8))
    for ax, (c, lab) in zip(axes, [("ES_VN", "ES 100% VN"), ("ES_5050", "ES 50/50"), ("ES_SP", "ES 100% S&P"),
                                   ("DR", "Lợi ích DR")]):
        data = [d.loc[d["regime"] == k, c].dropna() for k in ("Thấp", "Cao")]
        ax.boxplot(data, tick_labels=["Lạm phát thấp", "Lạm phát cao"], showfliers=False)
        ax.set_title(lab)
        pct(ax)
    fig.suptitle("F16. ES và lợi ích đa dạng hóa theo chế độ lạm phát (so sánh bối cảnh, không nhân quả)",
                 x=0.01, ha="left")
    fig.tight_layout()
    save(fig, "F16_inflation_regime_es", cfg)


def f17_component(cfg: dict) -> None:
    d = read_table("T9b_component_es")
    d = d[d["w_VN"] == 0.5].pivot(index="period", columns="component", values="CES") * 100
    fig, ax = plt.subplots(figsize=(9, 4))
    d.plot.bar(stacked=True, ax=ax, color=OKABE[:3], width=0.7)
    ax.set(title="F17. Component ES (Euler) danh mục 50/50: đóng góp VN / S&P (USD) / tỷ giá",
           ylabel="Đóng góp vào ES 97,5% (%/ngày)", xlabel="")
    ax.tick_params(axis="x", rotation=30)
    ax.axhline(0, color="black", lw=0.6)
    save(fig, "F17_component_es", cfg)


def f18_irf(cfg: dict) -> None:
    irf = np.load(path_of("processed", cfg) / "var_irf_orth.npy")
    names = ["S&P 500", "USD/VND", "VN-Index"]
    fig, axes = plt.subplots(1, 3, figsize=(11, 3.4), sharey=True)
    for j, ax in enumerate(axes):
        ax.bar(range(irf.shape[0]), irf[:, 2, j], color=OKABE[j])
        ax.axhline(0, color="black", lw=0.6)
        ax.set(title=f"Phản ứng của VN-Index trước cú sốc {names[j]}", xlabel="Số phiên sau cú sốc",
               ylabel="% (1 độ lệch chuẩn)")
    fig.suptitle("F18. Hàm phản ứng xung trực giao từ VAR (Bài 9)", x=0.01, ha="left")
    fig.tight_layout()
    save(fig, "F18_var_irf", cfg)


def f19_tail_corr(cfg: dict) -> None:
    d = read_table("T8b_tail_correlation")
    fig, ax = plt.subplots(figsize=(7, 4))
    for i, side in enumerate(["cùng giảm", "cùng tăng"]):
        s = d[d["side"] == side]
        ax.plot(s["q"], s["corr_emp"], marker="o", color=OKABE[i * 3], label=f"Thực tế — {side}")
        ax.plot(s["q"], s["corr_normal_implied"], ls="--", color=OKABE[i * 3], label=f"Normal hàm ý — {side}")
    ax.set(title="F19. Tương quan vượt ngưỡng VN–S&P (Longin–Solnik), S&P lệch pha t−1",
           xlabel="Phân vị ngưỡng q", ylabel="Tương quan có điều kiện")
    ax.legend(fontsize=7)
    save(fig, "F19_tail_correlation", cfg)


def run(cfg: dict | None = None) -> None:
    from .portfolio import load_returns
    from .rolling import load_forecasts

    cfg = cfg or load_config()
    prices = pd.read_parquet(path_of("processed", cfg) / "daily_prices.parquet")
    r = load_returns(cfg)
    fc = load_forecasts(cfg, "main")
    t5, t14 = read_table("T5_backtest_var"), read_table("T14_allocation_es_limits")
    f1_prices(prices, cfg)
    f2_returns(r, cfg)
    f3_f4_distribution(r, cfg)
    f5_acf(r, cfg)
    f6_inflation(cfg)
    f7_var_paths(fc, cfg)
    f8_crisis_zoom(fc, cfg)
    f9_exceed_counts(t5, cfg)
    f10_corr(cfg)
    f11_div(cfg)
    f12_es_weight(t14, cfg)
    f13_garch_vol(fc, cfg)
    f14_heatmap(t5, cfg)
    f16_inflation_es(cfg)
    f17_component(cfg)
    f18_irf(cfg)
    f19_tail_corr(cfg)
