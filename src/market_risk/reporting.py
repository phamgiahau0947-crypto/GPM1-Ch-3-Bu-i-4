"""Phase 11.4 — Xuất bảng ra Markdown và LaTeX (booktabs), định dạng số thống nhất; ghi câu trả lời MT."""

from __future__ import annotations

import logging

import pandas as pd

from .config import ROOT, load_config, path_of, read_table

log = logging.getLogger(__name__)

# Bảng chính cho báo cáo: (tên file, cột giữ lại, bộ lọc, tiêu đề)
KEY_TABLES = {
    "T1_descriptive": (["period", "label", "N", "mean_ann", "std_ann", "skew", "exkurt", "q01", "min"],
                       lambda d: d[d["period"] == "Toàn kỳ"], "Thống kê mô tả lợi suất ngày (toàn kỳ)"),
    "T2_assumption_tests": (["label", "test", "statistic", "p_value", "sig", "conclusion"], None,
                            "Kiểm định giả định của mô hình VaR"),
    "T3_garch_params": (["series", "model", "omega", "alpha", "beta", "persistence", "half_life_days",
                         "BIC"], None, "Tham số GARCH toàn kỳ"),
    "T4_var_es_overall": (["portfolio", "model", "VaR_95", "VaR_99", "ES_975", "diff_ES_975_vs_HS_pct", "ES_vs_VN100_pct"],
                          lambda d: d[d["sample"] == "common"], "VaR/ES dự báo trung bình (mẫu chung)"),
    "T5_backtest_var": (["portfolio", "model", "T", "x", "expected", "rate", "p_uc", "p_ind", "p_cc",
                         "conclusion"], lambda d: d[(d["set"] == "main") & (d["level"] == 0.99)], "Backtest VaR 99%"),
    "T8_diversification_by_corr": (["model", "corr_measure", "metric", "tercile", "N", "mean", "p_block_bootstrap"],
                                   lambda d: d[d["corr_measure"] == "corr_252"], "Lợi ích đa dạng hóa theo tương quan"),
    "T9_fx_effect": (["period", "portfolio", "model", "ES_VND", "ES_USD", "dES_FX", "corr_SPUSD_FX"],
                     lambda d: d[d["period"] == "Toàn kỳ"], "Tác động tỷ giá"),
    "T10_inflation_regimes": (["split", "metric", "mean_Thap", "mean_Cao", "diff_Cao_Thap", "p_block_bootstrap"],
                              lambda d: d[d["split"] == "ngưỡng 4%"], "Theo chế độ lạm phát"),
    "T11_stress_historical": (["period", "portfolio", "model", "N", "mean_ES975", "worst_loss", "exc99", "UR_VaR99",
                               "UR_ES"], lambda d: d[d["model"].isin(["HS", "Normal", "MC_Normal", "GARCH_N"])],
                              "Stress test lịch sử"),
    "T14_allocation_es_limits": (["model", "weight", "period", "ES_mean", "pct_days_ES_gt_4pct", "ret_to_ES"],
                                 lambda d: d[d["used_for_conclusion"]], "ES theo lưới tỷ trọng"),
    "T15_model_recommendation": (["model", "label", "n_pass_var99", "crisis_UR_VaR99",
                                  "complexity", "overall_rank", "verdict"], None, "Khuyến nghị mô hình"),
}


def fmt(df: pd.DataFrame) -> pd.DataFrame:
    """Định dạng số thống nhất: p-value 3 chữ số, tỷ lệ/lợi suất theo % 2 chữ số."""
    out = df.copy()
    for c in out.columns:
        if not pd.api.types.is_float_dtype(out[c]):
            continue
        if c.startswith("p_") or c.endswith("_p") or "pvalue" in c:
            out[c] = out[c].map(lambda v: "" if pd.isna(v) else ("<0,001" if v < 0.001 else f"{v:.3f}".replace(".", ",")))
        elif any(k in c for k in ("VaR", "ES", "mean", "std", "loss", "rate", "q0", "min", "ret", "vol", "DB", "DR")) \
                and "pct" not in c and "rank" not in c and "UR" not in c and "ratio" not in c:
            out[c] = out[c].map(lambda v: "" if pd.isna(v) else f"{100 * v:.2f}%".replace(".", ","))
        else:
            out[c] = out[c].map(lambda v: "" if pd.isna(v) else f"{v:.3f}".replace(".", ","))
    return out


def run(cfg: dict | None = None) -> None:
    cfg = cfg or load_config()
    out_md, out_tex = path_of("tables", cfg) / "markdown", path_of("tables", cfg) / "latex"
    out_md.mkdir(exist_ok=True)
    out_tex.mkdir(exist_ok=True)
    index = ["# Bảng kết quả chính (tự sinh)\n"]
    for name, (cols, filt, title) in KEY_TABLES.items():
        try:
            d = read_table(name)
        except FileNotFoundError:
            log.warning("Thiếu bảng %s", name)
            continue
        d = filt(d) if filt else d
        d = fmt(d[[c for c in cols if c in d.columns]])
        md = d.to_markdown(index=False)
        (out_md / f"{name}.md").write_text(f"## {title}\n\n{md}\n", encoding="utf-8")
        # pandas.to_latex dùng booktabs (\toprule, \midrule, \bottomrule); escape=True xử lý %, &, _
        tex = d.to_latex(index=False, escape=True, caption=title, label=f"tab:{name}", longtable=len(d) > 30)
        (out_tex / f"{name}.tex").write_text(tex, encoding="utf-8")
        index.append(f"- [{title}](markdown/{name}.md) — `{name}.csv`")
    (path_of("tables", cfg) / "INDEX.md").write_text("\n".join(index) + "\n", encoding="utf-8")


def write_answers(ans: dict[str, str], cfg: dict | None = None) -> None:
    """Ghi các đoạn trả lời MT tự sinh vào outputs/tables/MT_answers.md và docs/."""
    cfg = cfg or load_config()
    text = "# Câu trả lời tự sinh cho các mục tiêu nghiên cứu\n\n" + "\n\n".join(
        f"## {k}\n\n{v}" for k, v in ans.items()) + "\n"
    (path_of("tables", cfg) / "MT_answers.md").write_text(text, encoding="utf-8")
    (ROOT / "docs" / "MT_answers.md").write_text(text, encoding="utf-8")
