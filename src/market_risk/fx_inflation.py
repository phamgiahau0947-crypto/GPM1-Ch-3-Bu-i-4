"""Phase 7 — Vai trò tỷ giá và bối cảnh lạm phát (MT3). So sánh theo bối cảnh, KHÔNG nhân quả.

7.1 Tỷ giá: ES của S&P bằng USD (≈ phòng ngừa tỷ giá hoàn toàn) vs bằng VND;
    ΔES_FX = ES(VND) − ES(USD) (âm ⇒ tỷ giá đóng vai trò đệm); tương quan r_SP_USD với r_USDVND;
    component ES Euler (lịch sử) cho 3 nguồn VN / S&P (USD) / tỷ giá.
7.2 Lạm phát: ES, biến động, tương quan, DB, DR theo chế độ lạm phát (ngưỡng 4%, trung vị, tam phân vị);
    khác biệt Cao − Thấp kiểm định bằng block bootstrap.
7.3 Lợi suất thực theo tháng (mô tả).
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from .config import enabled_periods, load_config, path_of, save_table, stars
from .diversification import block_bootstrap_diff

log = logging.getLogger(__name__)


def es_hist(x: np.ndarray, q: float = 0.975) -> float:
    """ES lịch sử (dương = lỗ) của một mẫu lợi suất."""
    thr = np.quantile(x, 1 - q)
    return float(-x[x <= thr].mean())


def _periods(cfg: dict) -> dict[str, tuple]:
    return {"Toàn kỳ": (None, None)} | {k: (v["start"], v["end"]) for k, v in enabled_periods(cfg).items()}


def fx_effect(fc_main: pd.DataFrame, fc_usd: pd.DataFrame, returns: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """T9: ES bằng VND vs USD cho 100% S&P và 50/50 (rolling theo mô hình + lịch sử tĩnh)."""
    pairs = {"100% S&P": ("SP100", "SP_USD"), "50/50": ("VN50_SP50", "VN50_SP50_USD")}
    rows = []
    for pname, (a, b) in _periods(cfg).items():
        sub_r = returns.loc[a:b] if a else returns
        corr = sub_r["SP_USD"].corr(sub_r["USDVND"])
        for plab, (vnd, usd) in pairs.items():
            base = {"period": pname, "portfolio": plab, "corr_SPUSD_FX": corr}
            rows.append(base | {"model": "HS tĩnh (toàn giai đoạn)", "ES_VND": es_hist(sub_r[vnd].values),
                                "ES_USD": es_hist(sub_r[usd].values)})
            for m in cfg["models_main"]:
                ev = fc_main[(fc_main["model"] == m) & (fc_main["portfolio"] == vnd)].set_index("Date")["ES_975"]
                eu = fc_usd[(fc_usd["model"] == m) & (fc_usd["portfolio"] == usd)].set_index("Date")["ES_975"]
                j = pd.concat([ev, eu], axis=1, keys=["v", "u"]).dropna()
                j = j.loc[a:b] if a else j
                rows.append(base | {"model": f"{m} (rolling)", "ES_VND": j["v"].mean(), "ES_USD": j["u"].mean()})
    df = pd.DataFrame(rows)
    df["dES_FX"] = df["ES_VND"] - df["ES_USD"]
    df["dES_FX_pct"] = 100 * df["dES_FX"] / df["ES_USD"]
    df["conclusion"] = np.where(df["dES_FX"] < 0, "Tỷ giá đóng vai trò ĐỆM (ES bằng VND thấp hơn)",
                                "Tỷ giá LÀM TĂNG rủi ro đuôi khi quy đổi VND")
    return df


def component_es(returns: pd.DataFrame, cfg: dict, w_vn: float = 0.5, q: float = 0.975) -> pd.DataFrame:
    """Component ES theo Euler (lịch sử) cho danh mục w_VN/(1−w_VN), tái cân bằng ngày, lợi suất đơn.

    R_p = w R_VN + (1−w)[R_SP + R_FX + R_SP·R_FX];  CES_i = −E[c_i | R_p ≤ VaR],  Σ CES_i = ES(R_p).
    Tích chéo R_SP·R_FX gộp vào phần tỷ giá.
    """
    rows = []
    for pname, (a, b) in _periods(cfg).items():
        d = returns.loc[a:b] if a else returns
        R = np.expm1(d[["VN", "SP_USD", "USDVND"]])
        comp = pd.DataFrame({"VN-Index": w_vn * R["VN"], "S&P 500 (USD)": (1 - w_vn) * R["SP_USD"],
                             "Tỷ giá USD/VND": (1 - w_vn) * (R["USDVND"] + R["SP_USD"] * R["USDVND"])})
        rp = comp.sum(1)
        tail = rp <= rp.quantile(1 - q)
        ces = -comp[tail].mean()
        es = -rp[tail].mean()
        for k, v in ces.items():
            rows.append({"period": pname, "w_VN": w_vn, "component": k, "CES": v, "ES_total": es, "share_pct": 100 * v / es})
    return pd.DataFrame(rows)


def regime_frame(fc_main: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """Khung ngày: ES (mô hình chính), biến động 21 phiên, tương quan 63, DB, DR và các cột chế độ."""
    proc = path_of("processed", cfg)
    infl = pd.read_parquet(proc / "inflation_daily.parquet")
    div = pd.read_parquet(proc / "diversification_timeseries.parquet")
    div = div[div["model"] == cfg["diversification"]["primary_model"]]
    from .portfolio import load_returns

    r = load_returns(cfg)
    vol = r[["VN100", "VN50_SP50", "SP100"]].rolling(21).std().mul(np.sqrt(252)).add_prefix("vol21_")
    df = div[["ES_VN", "ES_5050", "ES_SP", "DB", "DR", "corr_63"]].join(vol).join(infl, how="left")
    return df


def regime_compare(df: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """T10: trung bình theo chế độ + khác biệt Cao − Thấp (block bootstrap). Bỏ ngày không có CPI."""
    metrics = ["ES_VN", "ES_5050", "ES_SP", "vol21_VN100", "vol21_VN50_SP50", "vol21_SP100", "corr_63", "DB", "DR"]
    rows = []
    for rcol, lab in (("regime", "ngưỡng 4%"), ("regime_median", "trung vị"), ("regime_tercile", "tam phân vị"),
                      ("regime_pub", "ngưỡng 4% — đã công bố (trễ 1 tháng)")):
        d = df.dropna(subset=[rcol])
        d = d[d[rcol].isin(["Cao", "Thấp", "Trung bình"])]
        for m in metrics:
            x = d[[m, rcol]].dropna()
            means = x.groupby(rcol)[m].mean()
            hi, lo = x.loc[x[rcol] == "Cao", m].values, x.loc[x[rcol] == "Thấp", m].values
            p = block_bootstrap_diff(hi, lo, cfg["diversification"]["block_len"], 2000, cfg["seed"])
            rows.append({"split": lab, "metric": m, "mean_Thap": means.get("Thấp"), "mean_TrungBinh": means.get("Trung bình"),
                         "mean_Cao": means.get("Cao"), "diff_Cao_Thap": hi.mean() - lo.mean(), "N_Cao": hi.size,
                         "N_Thap": lo.size, "p_block_bootstrap": p, "sig": stars(p)})
    return pd.DataFrame(rows)


def real_returns(returns: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """T10b: lợi suất danh nghĩa và thực theo tháng: r_thực = r_danh nghĩa − ln(1 + π_tháng)."""
    monthly = pd.read_csv(path_of("processed", cfg) / "cpi_inflation.csv", index_col=0, parse_dates=True,
                          encoding="utf-8-sig")
    m = returns[["VN100", "VN50_SP50", "SP100"]].resample("MS").sum()
    pi = np.log1p(monthly["inflation_mom"]).reindex(m.index)
    d = m.join(pi.rename("pi")).dropna()
    rows = []
    for c in ("VN100", "VN50_SP50", "SP100"):
        real = d[c] - d["pi"]
        rows.append({"portfolio": c, "N_months": len(d), "nominal_ann": 12 * d[c].mean(), "inflation_ann": 12 * d["pi"].mean(),
                     "real_ann": 12 * real.mean(), "real_vol_ann": real.std() * np.sqrt(12),
                     "pct_months_negative_real": 100 * (real < 0).mean()})
    return pd.DataFrame(rows)


def fx_robustness(returns: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    """T9c: so sánh kết quả trên toàn mẫu và mẫu con, cùng một bộ dữ liệu clean."""
    from .portfolio import build_portfolios

    def summarize(r: pd.DataFrame, lab: str) -> dict:
        p = build_portfolios(r, cfg["portfolios"]["main"])
        e = {k: es_hist(p[k].values) for k in p}
        return {"variant": lab, "N": len(r), "vol_FX_ann": r["USDVND"].std() * np.sqrt(252),
                "ES_VN100": e["VN100"], "ES_5050": e["VN50_SP50"], "ES_SP100": e["SP100"],
                "ES_SP_USD": es_hist(r["SP_USD"].values),
                "DR_static": 1 - e["VN50_SP50"] / (0.5 * e["VN100"] + 0.5 * e["SP100"])}

    return pd.DataFrame([
        summarize(returns, "Toàn mẫu (hai file clean)"),
        summarize(returns.loc["2014-01-01":], "Mẫu con từ 2014 (hai file clean)"),
    ])


def mt3_text(t9: pd.DataFrame, t10: pd.DataFrame, ces: pd.DataFrame) -> str:
    full = t9[(t9["period"] == "Toàn kỳ")]
    sp = full[full["portfolio"] == "100% S&P"]
    main = t10[t10["split"] == "ngưỡng 4%"].set_index("metric")
    c = ces[ces["period"] == "Toàn kỳ"].set_index("component")["share_pct"]
    return (
        f"- Toàn kỳ, ΔES_FX của 100% S&P = {100 * sp['dES_FX'].min():.2f} đến {100 * sp['dES_FX'].max():.2f} điểm %/ngày "
        f"tùy mô hình; tương quan r_S&P(USD) với r_USD/VND = {sp['corr_SPUSD_FX'].iloc[0]:.3f} — T9_fx_effect.\n"
        f"- Component ES (50/50, toàn kỳ): VN {c.get('VN-Index', np.nan):.1f}%, S&P (USD) {c.get('S&P 500 (USD)', np.nan):.1f}%, "
        f"tỷ giá {c.get('Tỷ giá USD/VND', np.nan):.1f}% tổng ES — T9b_component_es.\n"
        f"- Lạm phát cao (> 4%) trùng với ES 100% VN trung bình {100 * main.loc['ES_VN', 'mean_Cao']:.2f}% so với "
        f"{100 * main.loc['ES_VN', 'mean_Thap']:.2f}% khi lạm phát thấp (p = {main.loc['ES_VN', 'p_block_bootstrap']:.3f}); "
        f"DR trung bình {100 * main.loc['DR', 'mean_Cao']:.1f}% vs {100 * main.loc['DR', 'mean_Thap']:.1f}% — T10_inflation_regimes.\n"
        "- Đây là so sánh theo bối cảnh: các tháng lạm phát cao trùng với những cú sốc khác (2008, 2011, 2022) nên "
        "không tách được tác động riêng của lạm phát."
    )


def run(cfg: dict | None = None) -> str:
    from .portfolio import load_returns
    from .rolling import load_forecasts

    cfg = cfg or load_config()
    returns = load_returns(cfg)
    fc_main, fc_usd = load_forecasts(cfg, "main"), load_forecasts(cfg, "usd")
    t9 = fx_effect(fc_main, fc_usd, returns, cfg)
    ces = pd.concat([component_es(returns, cfg, w) for w in (0.5, 0.0)], ignore_index=True)
    reg = regime_frame(fc_main, cfg)
    reg.to_parquet(path_of("processed", cfg) / "regime_frame.parquet")
    t10 = regime_compare(reg, cfg)
    save_table(t9, "T9_fx_effect")
    save_table(ces, "T9b_component_es")
    save_table(t10, "T10_inflation_regimes")
    save_table(real_returns(returns, cfg), "T10b_real_returns")
    save_table(fx_robustness(returns, cfg), "T9c_clean_sample_robustness")
    return mt3_text(t9, t10, ces[ces["w_VN"] == 0.5])
