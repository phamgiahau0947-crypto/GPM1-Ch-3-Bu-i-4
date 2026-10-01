"""Phase 9 — Application: so sánh lưới tỷ trọng với giới hạn ES và khuyến nghị lựa chọn mô hình.

Khung tham chiếu: ES/CVaR trong quản trị danh mục (Rockafellar & Uryasev 2000, 2002) — nhưng KHÔNG giải
bài toán tối ưu; chỉ so sánh 5 tỷ trọng cố định. Khuyến nghị định tính, không nêu % cụ thể,
và chỉ dựa trên mô hình đã vượt backtest (Phase 5).
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from .backtest.runner import pass_table
from .config import ROOT, enabled_periods, load_config, read_table, save_table, stress_mask
from .models import MODEL_LABELS, MODEL_TIER

log = logging.getLogger(__name__)
GRID_SOURCE = {"W100_0": "VN100", "W75_25": "W75_25", "W50_50": "VN50_SP50", "W25_75": "W25_75", "W0_100": "SP100"}
GRID_LABEL = {"W100_0": "100/0", "W75_25": "75/25", "W50_50": "50/50", "W25_75": "25/75", "W0_100": "0/100"}

# Điểm định tính (1 = tốt nhất, 5 = kém nhất) — do nhóm đánh giá, cần giải thích khi vấn đáp
COMPLEXITY = {"HS": 1, "Normal": 1, "MC_Normal": 2, "GARCH_N": 3}
EXPLAIN = {"HS": 1, "Normal": 1, "MC_Normal": 2, "GARCH_N": 3}


def eligible_models(cfg: dict) -> tuple[list[str], pd.DataFrame, str]:
    """Chọn phương pháp dựa duy nhất trên Kupiec và Christoffersen ở VaR 99%."""
    pt = pass_table(read_table("T5_backtest_var"), cfg["backtest"]["alpha_test"])
    n_pass = pt.groupby("model")["pass_all"].sum().reindex(cfg["models_main"], fill_value=0)
    if n_pass.max() == 0:
        chosen = []
        note = ("CẢNH BÁO: không phương pháp nào đồng thời vượt qua Kupiec và Christoffersen "
                "ở VaR 99% trong các danh mục chính.")
    else:
        chosen = n_pass[n_pass == n_pass.max()].index.tolist()
        note = (f"{', '.join(MODEL_LABELS[m] for m in chosen)} không bị bác bỏ bởi Kupiec và Christoffersen "
                f"ở VaR 99% trong {int(n_pass.max())}/3 danh mục chính.")
    return chosen, pt, note


def grid_table(fc_all: pd.DataFrame, returns: pd.DataFrame, models: list[str], cfg: dict) -> pd.DataFrame:
    """T14: ES theo tỷ trọng × giai đoạn, % ngày ES vượt giới hạn L, lợi suất/ES."""
    rows = []
    limits = cfg["application"]["es_limits"]
    for m in models:
        for w, src in GRID_SOURCE.items():
            g = fc_all[(fc_all["model"] == m) & (fc_all["portfolio"] == src) & fc_all["set"].isin(["main", "grid"])]
            g = g.set_index("Date")
            sm = stress_mask(g.index, cfg)
            parts = {"Toàn kỳ": g, "Bình thường": g[~sm.values]} | {
                k: g.loc[p["start"]:p["end"]] for k, p in enabled_periods(cfg).items()}
            for pname, d in parts.items():
                if d.empty:
                    continue
                rec = {"model": m, "weight": GRID_LABEL[w], "w_VN": cfg["portfolios"]["grid"][w][0], "period": pname,
                       "N": len(d), "ES_mean": d["ES_975"].mean(), "ES_p95": d["ES_975"].quantile(0.95),
                       "ret_ann": d["realized"].mean() * 252, "vol_ann": d["realized"].std() * np.sqrt(252),
                       "ret_to_ES": d["realized"].mean() / d["ES_975"].mean()}
                for L in limits:
                    rec[f"pct_days_ES_gt_{int(L * 100)}pct"] = 100 * (d["ES_975"] > L).mean()
                rows.append(rec)
    return pd.DataFrame(rows)


def consistency(t14: pd.DataFrame, cfg: dict, tol_pct: float = 5.0) -> pd.DataFrame:
    """Tỷ trọng 'thỏa L' (≤ 5% số ngày ES > L) trong giai đoạn bình thường có còn thỏa trong khủng hoảng?"""
    rows = []
    for L in cfg["application"]["es_limits"]:
        col = f"pct_days_ES_gt_{int(L * 100)}pct"
        for (m, w), g in t14.groupby(["model", "weight"]):
            g = g.set_index("period")
            normal_ok = g.loc["Bình thường", col] <= tol_pct
            rec = {"model": m, "weight": w, "limit_L": L, "ok_normal": normal_ok}
            for k in cfg["core_stress"]:
                if k in g.index:
                    rec[f"ok_{k}"] = g.loc[k, col] <= tol_pct
            rec["consistent"] = normal_ok and all(v for kk, v in rec.items() if kk.startswith("ok_") and kk != "ok_normal")
            rows.append(rec)
    return pd.DataFrame(rows)


def model_recommendation(cfg: dict) -> pd.DataFrame:
    """T15: xếp hạng theo hai kiểm định VaR, mức thiếu dự báo khi stress và độ đơn giản."""
    pt = pass_table(read_table("T5_backtest_var"), cfg["backtest"]["alpha_test"])
    t11 = read_table("T11_stress_historical")
    rt = read_table("T4b_rolling_runtime")
    rt = rt[rt["set"] == "main"].groupby("model")["seconds"].mean()
    core = t11[t11["period"].isin(cfg["core_stress"])]
    df = pd.DataFrame({
        "n_pass_var99": pt.groupby("model")["pass_all"].sum(),
        "crisis_UR_VaR99": core.groupby("model")["UR_VaR99"].mean(),
        "runtime_s": rt,
    })
    df["complexity"] = df.index.map(COMPLEXITY)
    df["explainability"] = df.index.map(EXPLAIN)
    df["crisis_gap"] = (df["crisis_UR_VaR99"] - 1).abs()
    ranks = pd.DataFrame({
        "r_backtest": (-df["n_pass_var99"]).rank(),
        "r_crisis": df["crisis_gap"].rank(),
        "r_simple": (df["complexity"] + df["explainability"]).rank(),
    })
    weights = {"r_backtest": 0.60, "r_crisis": 0.25, "r_simple": 0.15}
    df["score"] = sum(ranks[k] * v for k, v in weights.items())
    df["overall_rank"] = df["score"].rank(method="min")
    df["label"] = df.index.map(MODEL_LABELS)
    df["tier"] = df.index.map(MODEL_TIER)
    df["verdict"] = np.select(
        [df["n_pass_var99"] >= 2, df["n_pass_var99"] >= 1],
        ["Ứng viên mô hình chính (không bị bác bỏ ở ≥ 2/3 danh mục theo hai kiểm định VaR)",
         "Cân nhắc thận trọng (không bị bác bỏ ở một danh mục theo hai kiểm định VaR)"],
        "Chưa được hai kiểm định VaR ủng hộ")
    return df.reset_index(names="model").sort_values("overall_rank")


ORDER = ["100/0", "75/25", "50/50", "25/75", "0/100"]


def _es_pivot(t14: pd.DataFrame, m: str) -> pd.DataFrame:
    return (t14[t14["model"] == m].pivot(index="weight", columns="period", values="ES_mean") * 100).reindex(ORDER)


def _lean_sentence(d: pd.DataFrame) -> tuple[str, str]:
    """Câu mô tả tỷ trọng có ES thấp nhất theo từng giai đoạn và hướng nghiêng (tự sinh từ số liệu)."""
    best = d.idxmin()
    per = "; ".join(f"{c}: {best[c]} ({d[c].min():.2f}%)" for c in d.columns)
    idx = [ORDER.index(best[c]) for c in d.columns if c not in ("Toàn kỳ",)]
    share_us = np.mean([i >= 2 for i in idx])
    lean = ("phía Mỹ (tăng tỷ trọng S&P 500) so với danh mục thuần VN-Index" if share_us >= 0.5
            else "phía Việt Nam")
    pure_min = d.loc[["100/0", "0/100"]].min()
    mixed_min = d.loc[["75/25", "50/50", "25/75"]].min()
    n_mix = int((mixed_min < pure_min).sum())
    mix = (f"Ở {n_mix}/{d.shape[1]} giai đoạn, ít nhất một tỷ trọng kết hợp có ES thấp hơn CẢ HAI danh mục thuần "
           "(nhất quán với tính dưới cộng tính của ES).")
    return f"Tỷ trọng có ES thấp nhất theo giai đoạn — {per}. {mix}", lean


def application_text(t14: pd.DataFrame, cons: pd.DataFrame, models: list[str], note: str, t15: pd.DataFrame,
                     cfg: dict) -> str:
    """Bản nháp diễn giải tự sinh (docs/application_draft.md) — định hướng, KHÔNG nêu tỷ trọng %."""
    m = models[0] if models else str(t15.iloc[0]["model"])
    d = _es_pivot(t14, m)
    per_text, lean = _lean_sentence(d)
    vn_side = [c for c in d.columns if ORDER.index(d[c].idxmin()) < 2]
    exceptions = (f"Ngoại lệ — các giai đoạn mà tỷ trọng có ES thấp nhất nghiêng về VN: {', '.join(vn_side)}; "
                  "tức là lợi ích của việc thêm S&P phụ thuộc vào việc cú sốc bắt nguồn từ thị trường nào."
                  if vn_side else "Không có giai đoạn nào mà tỷ trọng thiên về VN cho ES thấp nhất.")
    missing = [k for k in cfg["core_stress"] if k not in d.columns]
    cover = ""
    if missing:
        alt = "HS" if "HS" in t14["model"].unique() else cfg["models_main"][0]
        da = _es_pivot(t14, alt)
        cover = (f" Mô hình {MODEL_LABELS[m]} cần cửa sổ dài nên không phủ {', '.join(missing)}; đối chiếu bằng "
                 f"{MODEL_LABELS[alt]}: " + "; ".join(f"{k}: thấp nhất tại {da[k].idxmin()} ({da[k].min():.2f}%)"
                                                     for k in missing if k in da) + ".")
    c4 = cons[(cons["model"] == m) & (cons["limit_L"] == 0.04)]
    cons_w = ", ".join(c4.loc[c4["consistent"], "weight"]) or "không có tỷ trọng nào"
    normal_w = ", ".join(c4.loc[c4["ok_normal"], "weight"]) or "không có"
    top = ", ".join(f"{r.label}" for r in t15.head(3).itertuples())
    t9, t10 = read_table("T9_fx_effect"), read_table("T10_inflation_regimes")
    fx = t9[(t9["period"] == "Toàn kỳ") & (t9["portfolio"] == "100% S&P")]["dES_FX"] * 100
    fx_txt = (f"ES của 100% S&P tính bằng VND cao hơn tính bằng USD {fx.min():.2f}–{fx.max():.2f} điểm %/ngày (toàn kỳ, T9)"
              if (fx > 0).all() else f"ΔES do tỷ giá dao động {fx.min():.2f} đến {fx.max():.2f} điểm %/ngày (T9)")
    inf = t10[(t10["split"] == "ngưỡng 4%") & (t10["metric"] == "ES_VN")].iloc[0]
    inf_txt = (f"ES 100% VN trung bình {100 * inf['mean_Cao']:.2f}% khi lạm phát > 4% so với {100 * inf['mean_Thap']:.2f}% "
               f"khi lạm phát thấp (p = {inf['p_block_bootstrap']:.3f}, T10)")
    q = read_table("T0_data_quality").set_index("series")
    n_fx = int(q.loc["USDVND", "n_flagged_errors"])
    span = f"{pd.Timestamp(q.loc['MERGED (inner)', 'start']):%m/%Y}–{pd.Timestamp(q.loc['MERGED (inner)', 'end']):%m/%Y}"
    model_scope = (f"Mô hình dùng để đo: **{', '.join(MODEL_LABELS[x] for x in models)}**."
                   if models else
                   f"**CẢNH BÁO:** Không có phương pháp nào đồng thời được cả Kupiec và Christoffersen ủng hộ ở VaR 99%. "
                   f"{MODEL_LABELS[m]} chỉ được dùng để mô tả kết quả thăm dò, không làm căn cứ kết luận.")
    direction = (f"Nhìn chung kết quả **nghiêng về {lean}**."
                 if models else
                 f"Kết quả thăm dò **nghiêng về {lean}**, nhưng không đủ điều kiện để đưa ra kết luận.")
    return f"""# Application — Phân bổ theo giới hạn ES (bản nháp tự sinh)

> {model_scope}{(" " + note) if models else ""}
> Số liệu: `outputs/tables/T14_allocation_es_limits.csv`, `T14b_allocation_consistency.csv`, `T15_model_recommendation.csv`.

**(a) Kết quả {'nghiêng về phía nào' if models else 'thăm dò — chưa đủ điều kiện kết luận'}.**
Theo {MODEL_LABELS[m]} (ES 97,5% trung bình, %/ngày): {per_text}{cover}
{direction} {exceptions}

**(b) Backtest có ủng hộ kết luận không.** {note} Các phương pháp xếp hạng đầu theo hai kiểm định VaR và mức thiếu dự báo khi stress (T15): {top}.

**(c) Điều kiện làm kết luận thay đổi.** Lợi ích đa dạng hóa **đi kèm với** mức tương quan VN–Mỹ: khi tương quan tăng,
lợi ích thu hẹp (MT2, T8). Với giới hạn minh họa ES 4%/ngày: tỷ trọng thỏa giới hạn lúc bình thường (≤ 5% số ngày vượt): {normal_w};
vẫn thỏa trong mọi giai đoạn stress lõi có dữ liệu: {cons_w} (T14b). Về tỷ giá: {fx_txt}. Về lạm phát: {inf_txt} —
so sánh theo bối cảnh, không nhân quả.

**(d) Hạn chế.** Chỉ số không phải tài sản đầu tư trực tiếp (cần ETF/quỹ, có sai lệch theo dõi); bỏ qua phí, thuế và
hạn chế chuyển vốn ra nước ngoài của nhà đầu tư cá nhân Việt Nam; chuỗi tỷ giá có {n_fx} điểm lỗi báo giá đã được lọc
(T0_fx_cleaning_log); kết quả dựa trên dữ liệu quá khứ {span} và không đảm bảo cho tương lai.

*Không nêu tỷ trọng % khuyến nghị — chỉ nêu định hướng (CLAUDE.md §2).*
"""


def run(cfg: dict | None = None) -> str:
    from .portfolio import load_returns
    from .rolling import load_forecasts

    cfg = cfg or load_config()
    models, pt, note = eligible_models(cfg)
    fc_all = load_forecasts(cfg, None)
    t14 = grid_table(fc_all, load_returns(cfg), cfg["models_main"], cfg)
    t14["used_for_conclusion"] = t14["model"].isin(models)
    cons = consistency(t14, cfg)
    t15 = model_recommendation(cfg)
    save_table(pt, "T5b_pass_table")
    save_table(t14, "T14_allocation_es_limits")
    save_table(cons, "T14b_allocation_consistency")
    save_table(t15, "T15_model_recommendation")
    text = application_text(t14, cons, models, note, t15, cfg)
    (ROOT / "docs" / "application_draft.md").write_text(text, encoding="utf-8")
    return text
