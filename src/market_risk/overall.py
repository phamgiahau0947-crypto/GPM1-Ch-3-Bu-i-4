"""Phase 3.12–3.13 — Tham số GARCH toàn kỳ (T3) và VaR/ES theo mô hình × danh mục (T4) — MT1."""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from .config import load_config, save_table
from .models import MODEL_LABELS, MODEL_TIER, MODELS
from .models.garch import SCALE, fit_garch

log = logging.getLogger(__name__)
MAIN = ["VN100", "VN50_SP50", "SP100"]
PORT_LABEL = {"VN100": "100% VN", "VN50_SP50": "50/50", "SP100": "100% S&P (VND)",
              "W75_25": "75/25", "W25_75": "25/75", "SP_USD": "100% S&P (USD)", "VN50_SP50_USD": "50/50 (S&P USD)"}


def garch_param_table(returns: pd.DataFrame, series: list[str]) -> pd.DataFrame:
    """T3: ước lượng tham số và độ dai dẳng của GARCH(1,1) trên toàn kỳ."""
    rows = []
    for s in series:
        r = returns[s].values
        fit, res = fit_garch(r)
        n, k = len(r), res.params.size
        ll = res.loglikelihood + n * np.log(SCALE)
        pers = fit.persistence
        rows.append({
            "series": s, "model": "GARCH_N", "mu": fit.mu / SCALE, "omega": fit.omega / SCALE**2,
            "alpha": fit.alpha, "beta": fit.beta,
            "persistence": pers, "half_life_days": np.log(0.5) / np.log(pers) if pers < 1 - 1e-6 else np.inf,  # α+β ≈ 1: cú sốc không tắt dần
            "uncond_vol_ann": np.sqrt(fit.omega / (1 - pers) * 252) / SCALE if pers < 1 - 1e-6 else np.nan,
            "loglik": ll, "AIC": -2 * ll + 2 * k, "BIC": -2 * ll + k * np.log(n),
        })
    df = pd.DataFrame(rows)
    return df


def overall_var_es(fc: pd.DataFrame) -> pd.DataFrame:
    """T4: trung bình VaR/ES dự báo rolling theo mô hình × danh mục + chênh lệch so với HS.

    Tính trên toàn bộ dự báo và mẫu chung để so sánh công bằng giữa bốn phương pháp.
    """
    cols = ["VaR_95", "VaR_975", "VaR_99", "ES_975"]
    wide_n = fc.groupby(["Date", "portfolio"])["model"].transform("count")
    common = fc[wide_n == fc["model"].nunique()]
    out = []
    for lab, d in (("own", fc), ("common", common)):
        g = d.groupby(["portfolio", "model"])[cols + ["realized"]].agg(["mean"]).droplevel(1, axis=1)
        g["N"] = d.groupby(["portfolio", "model"]).size()
        g["start"] = d.groupby(["portfolio", "model"])["Date"].min().dt.date
        g["sample"] = lab
        out.append(g.reset_index())
    df = pd.concat(out, ignore_index=True)
    hs = df[df["model"] == "HS"].set_index(["sample", "portfolio"])
    for c in ("ES_975", "VaR_99"):
        base = df.set_index(["sample", "portfolio"]).index.map(hs[c])
        df[f"diff_{c}_vs_HS_pct"] = 100 * (df[c].values / np.asarray(base) - 1)
    vn = df[df["portfolio"] == "VN100"].set_index(["sample", "model"])["ES_975"]
    df["ES_vs_VN100_pct"] = 100 * (df["ES_975"].values / np.asarray(df.set_index(["sample", "model"]).index.map(vn)) - 1)
    df["label"] = df["model"].map(MODEL_LABELS)
    df["tier"] = df["model"].map(MODEL_TIER)
    df["portfolio_label"] = df["portfolio"].map(PORT_LABEL)
    return df


def static_full_sample(returns: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """T4a: VaR/ES ước lượng một lần trên TOÀN mẫu (mô hình phi điều kiện) và dự báo 1 ngày
    tại ngày cuối mẫu (mô hình có điều kiện) — bổ sung cho T4."""
    rk = cfg["risk"]
    rows = []
    for p in MAIN:
        r = returns[p].values
        for m, f in MODELS.items():
            kw = {"n_paths": rk["mc_paths"], "seed": cfg["seed"]}
            o = f(r, tuple(rk["var_levels"]), rk["es_level"], **kw)
            rows.append({"portfolio": p, "model": m, **{k: v for k, v in o.items() if k != "params"},
                         "type": "có điều kiện (dự báo ngày kế tiếp)" if m == "GARCH_N" else "phi điều kiện (toàn kỳ)"})
    return pd.DataFrame(rows)


def mt1_text(t4: pd.DataFrame) -> str:
    """Đoạn trả lời MT1 tự sinh từ T4 (mẫu chung)."""
    d = t4[t4["sample"] == "common"].pivot(index="model", columns="portfolio", values="ES_975") * 100
    red = (1 - d["VN50_SP50"] / d["VN100"]) * 100
    spread = d.max() - d.min()
    lines = [
        f"- ES 97,5% trung bình (mẫu chung) của danh mục 50/50 thấp hơn 100% VN ở {int((red > 0).sum())}/{len(red)} "
        f"phương pháp; mức giảm trung vị {red.median():.1f}% (từ {red.min():.1f}% đến {red.max():.1f}%) — T4_var_es_overall.",
        f"- ES trung bình 100% VN: {d['VN100'].median():.2f}%/ngày; 50/50: {d['VN50_SP50'].median():.2f}%; "
        f"100% S&P (VND): {d['SP100'].median():.2f}% (trung vị qua các mô hình).",
        f"- Chênh lệch giữa mô hình cao nhất và thấp nhất: VN {spread['VN100']:.2f} điểm %, 50/50 {spread['VN50_SP50']:.2f}, "
        f"S&P {spread['SP100']:.2f} → lựa chọn mô hình quan trọng không kém lựa chọn tỷ trọng.",
    ]
    return "\n".join(lines)


def run(cfg: dict | None = None) -> str:
    from .portfolio import load_returns
    from .rolling import load_forecasts

    cfg = cfg or load_config()
    returns = load_returns(cfg)
    save_table(garch_param_table(returns, MAIN + ["SP_USD", "USDVND"]), "T3_garch_params")
    t4 = overall_var_es(load_forecasts(cfg, "main"))
    save_table(t4, "T4_var_es_overall")
    save_table(static_full_sample(returns, cfg), "T4a_var_es_static")
    return mt1_text(t4)
