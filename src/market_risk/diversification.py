"""Phase 6 — Lợi ích đa dạng hóa theo thời gian (MT2). Phân tích MÔ TẢ, không nhân quả.

* Tương quan trượt VN–S&P(VND) 63 và 252 phiên, EWMA (λ = 0,94), DCC(1,1) hai bước (Engle 2002).
* Lợi ích đa dạng hóa từ ES rolling:
      DB_t = ES_t(100% VN) − ES_t(50/50)                              (tuyệt đối)
      DR_t = 1 − ES_t(50/50) / [0,5·ES_t(VN) + 0,5·ES_t(S&P)]         (tương đối; ES dưới cộng tính ⇒ DR ≥ 0)
* So sánh theo tam phân vị tương quan (Welch, Mann–Whitney, block bootstrap), hồi quy Newey–West.
* Tương quan trong đuôi (Longin & Solnik 2001) so với mức Normal hàm ý; hiệu chỉnh Forbes–Rigobon (2002).
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
import statsmodels.api as sm
from arch import arch_model
from scipy import optimize, stats

from .config import enabled_periods, load_config, path_of, save_table, stars

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tương quan theo thời gian
# ---------------------------------------------------------------------------
def ewma_corr(x: pd.Series, y: pd.Series, lam: float = 0.94) -> pd.Series:
    """Tương quan EWMA: cov_t = λ cov_{t−1} + (1−λ) x_t y_t (tương tự cho phương sai), μ = 0."""
    a = np.column_stack([x.values, y.values])
    init = np.cov(a[:30].T, ddof=0) + np.outer(a[:30].mean(0), a[:30].mean(0))
    S = init.copy()
    out = np.empty(len(a))
    for t, v in enumerate(a):
        S = lam * S + (1 - lam) * np.outer(v, v)
        out[t] = S[0, 1] / np.sqrt(S[0, 0] * S[1, 1])
    return pd.Series(out, index=x.index, name="corr_ewma")


def _dcc_nll(params: np.ndarray, z: np.ndarray, Qbar: np.ndarray) -> float:
    a, b = params
    if a < 0 or b < 0 or a + b >= 0.999:
        return 1e10
    Q = Qbar.copy()
    nll = 0.0
    for t in range(z.shape[0]):
        if t > 0:
            Q = (1 - a - b) * Qbar + a * np.outer(z[t - 1], z[t - 1]) + b * Q
        d = 1 / np.sqrt(np.diag(Q))
        R = Q * np.outer(d, d)
        det = R[0, 0] * R[1, 1] - R[0, 1] ** 2
        inv_quad = (R[1, 1] * z[t, 0] ** 2 - 2 * R[0, 1] * z[t, 0] * z[t, 1] + R[0, 0] * z[t, 1] ** 2) / det
        nll += 0.5 * (np.log(det) + inv_quad - z[t] @ z[t])
    return nll


def dcc_garch(x: pd.Series, y: pd.Series) -> tuple[pd.Series, dict]:
    """DCC(1,1) hai bước (Engle 2002), tự viết bằng scipy (arch không có DCC).

    Bước 1: GARCH(1,1)-t cho từng chuỗi → phần dư chuẩn hóa z.
    Bước 2: Q_t = (1−a−b) Q̄ + a z_{t−1} z'_{t−1} + b Q_{t−1};  R_t = diag(Q_t)^{−½} Q_t diag(Q_t)^{−½};
            cực đại log-likelihood tương quan −½ Σ (ln|R_t| + z'_t R_t^{−1} z_t − z'_t z_t).
    Ước lượng trên TOÀN mẫu → dùng để MÔ TẢ, không dùng để dự báo.
    """
    zs = []
    for s in (x, y):
        res = arch_model(s.values * 100, mean="Constant", vol="GARCH", p=1, q=1, dist="t").fit(disp="off")
        zs.append(np.asarray(res.std_resid))
    z = np.column_stack(zs)
    Qbar = np.cov(z.T, ddof=0)
    # Đa điểm khởi đầu: hàm likelihood DCC có cực trị địa phương (một lần chạy từ (0,03; 0,95)
    # đã hội tụ về a + b ≈ 0,07 trong khi (0,005; 0,99) cho likelihood cao hơn) → quét lưới rồi Nelder–Mead.
    grid = [(a0, b0) for a0 in (0.002, 0.005, 0.01, 0.02, 0.05) for b0 in (0.80, 0.90, 0.95, 0.98, 0.99)
            if a0 + b0 < 0.999]
    start = min(grid, key=lambda p: _dcc_nll(np.array(p), z, Qbar))
    best = optimize.minimize(_dcc_nll, start, args=(z, Qbar), method="Nelder-Mead",
                             options={"xatol": 1e-6, "fatol": 1e-6})
    a, b = best.x
    Q, rho = Qbar.copy(), np.empty(len(z))
    for t in range(len(z)):
        if t > 0:
            Q = (1 - a - b) * Qbar + a * np.outer(z[t - 1], z[t - 1]) + b * Q
        rho[t] = Q[0, 1] / np.sqrt(Q[0, 0] * Q[1, 1])
    return pd.Series(rho, index=x.index, name="corr_dcc"), {"a": a, "b": b, "a+b": a + b, "nll": best.fun}


def corr_timeseries(returns: pd.DataFrame, lagged: pd.DataFrame, cfg: dict) -> tuple[pd.DataFrame, dict]:
    """Bảng tương quan theo ngày (thông tin đến hết ngày t)."""
    dc = cfg["diversification"]
    x, y = returns["VN"], returns["SP_VND"]
    out = pd.DataFrame(index=returns.index)
    for w in dc["corr_windows"]:
        out[f"corr_{w}"] = x.rolling(w).corr(y)
        out[f"corr_lag_{w}"] = lagged["VN"].rolling(w).corr(lagged["SP_VND"]).reindex(out.index)
    out["corr_ewma"] = ewma_corr(x, y, dc["ewma_lambda"])
    out["corr_dcc"], par_sync = dcc_garch(x, y)
    lag_dcc, par_lag = dcc_garch(lagged["VN"], lagged["SP_VND"])
    out["corr_dcc_lag"] = lag_dcc.reindex(out.index)
    return out, [par_sync | {"data": "đồng thời"}, par_lag | {"data": "lệch pha (S&P t−1)"}]


# ---------------------------------------------------------------------------
# Lợi ích đa dạng hóa
# ---------------------------------------------------------------------------
def diversification_benefit(fc: pd.DataFrame, model: str) -> pd.DataFrame:
    """DB_t, DR_t từ ES rolling của một mô hình (ba danh mục chính)."""
    es = fc[fc["model"] == model].pivot(index="Date", columns="portfolio", values="ES_975")
    es = es[["VN100", "VN50_SP50", "SP100"]].dropna()
    return pd.DataFrame({"ES_VN": es["VN100"], "ES_5050": es["VN50_SP50"], "ES_SP": es["SP100"],
                         "DB": es["VN100"] - es["VN50_SP50"],
                         "DR": 1 - es["VN50_SP50"] / (0.5 * es["VN100"] + 0.5 * es["SP100"])})


def block_bootstrap_diff(a: np.ndarray, b: np.ndarray, block: int, reps: int, seed: int) -> float:
    """p-value hai phía cho khác biệt trung bình mean(a) − mean(b) bằng moving block bootstrap
    trên từng nhóm đã trừ trung bình (giữ tự tương quan trong nhóm)."""
    rng = np.random.default_rng(seed)
    obs = a.mean() - b.mean()

    def resample(x: np.ndarray) -> np.ndarray:
        x = x - x.mean()
        n = x.size
        k = int(np.ceil(n / block))
        starts = rng.integers(0, max(n - block, 1), size=(reps, k))
        idx = (starts[:, :, None] + np.arange(block)).reshape(reps, -1)[:, :n] % n
        return x[idx].mean(1)

    diff = resample(a) - resample(b)
    return float(np.mean(np.abs(diff) >= abs(obs)))


def tercile_analysis(df: pd.DataFrame, corr_col: str, cfg: dict) -> pd.DataFrame:
    """DB, DR trung bình theo tam phân vị tương quan + kiểm định khác biệt Cao vs Thấp."""
    d = df.dropna(subset=[corr_col, "DR"]).copy()
    d["tercile"] = pd.qcut(d[corr_col], 3, labels=["Thấp", "Trung bình", "Cao"])
    rows = []
    for metric in ("DB", "DR"):
        g = d.groupby("tercile", observed=True)
        for lab, sub in g:
            rows.append({"corr_measure": corr_col, "metric": metric, "tercile": lab, "N": len(sub),
                         "corr_mean": sub[corr_col].mean(), "mean": sub[metric].mean(), "median": sub[metric].median()})
        lo, hi = d.loc[d["tercile"] == "Thấp", metric].values, d.loc[d["tercile"] == "Cao", metric].values
        welch = stats.ttest_ind(hi, lo, equal_var=False)
        mw = stats.mannwhitneyu(hi, lo)
        reps = (
            cfg.get("diversification", {}).get("bootstrap_reps")
            or cfg.get("backtest", {}).get("bootstrap_reps", 5000)
        )
        pb = block_bootstrap_diff(hi, lo, cfg["diversification"]["block_len"], reps, cfg["seed"])
        rows.append({"corr_measure": corr_col, "metric": metric, "tercile": "Cao − Thấp", "N": len(hi) + len(lo),
                     "mean": hi.mean() - lo.mean(), "welch_t": welch.statistic, "p_welch": welch.pvalue,
                     "p_mannwhitney": mw.pvalue, "p_block_bootstrap": pb, "sig": stars(pb)})
    return pd.DataFrame(rows)


def nw_regression(df: pd.DataFrame, corr_col: str, y: str = "DR") -> dict:
    """Hồi quy mô tả y_t = a + b·ρ_t + e_t, sai số Newey–West (HAC, lag = 21)."""
    d = df[[y, corr_col]].dropna()
    res = sm.OLS(d[y], sm.add_constant(d[corr_col])).fit(cov_type="HAC", cov_kwds={"maxlags": 21})
    return {"y": y, "x": corr_col, "a": res.params.iloc[0], "b": res.params.iloc[1], "t_b_NW": res.tvalues.iloc[1],
            "p_b_NW": res.pvalues.iloc[1], "R2": res.rsquared, "N": int(res.nobs), "sig": stars(res.pvalues.iloc[1])}


# ---------------------------------------------------------------------------
# Tương quan trong đuôi
# ---------------------------------------------------------------------------
def exceedance_corr(x: np.ndarray, y: np.ndarray, q: float, side: str) -> tuple[float, int]:
    """Tương quan có điều kiện khi CẢ HAI thị trường cùng dưới phân vị q (side='down') hoặc trên 1−q."""
    if side == "down":
        m = (x <= np.quantile(x, q)) & (y <= np.quantile(y, q))
    else:
        m = (x >= np.quantile(x, 1 - q)) & (y >= np.quantile(y, 1 - q))
    return (float(np.corrcoef(x[m], y[m])[0, 1]) if m.sum() > 5 else np.nan), int(m.sum())


def tail_correlation(x: pd.Series, y: pd.Series, qs: list[float], seed: int) -> pd.DataFrame:
    """Longin–Solnik: tương quan vượt ngưỡng thực tế vs mức hàm ý của Normal hai chiều cùng ρ."""
    rho = x.corr(y)
    rng = np.random.default_rng(seed)
    sim = rng.multivariate_normal([0, 0], [[1, rho], [rho, 1]], size=500_000)
    rows = []
    for q in qs:
        for side in ("down", "up"):
            c, n = exceedance_corr(x.values, y.values, q, side)
            cn, _ = exceedance_corr(sim[:, 0], sim[:, 1], q, side)
            rows.append({"q": q, "side": "cùng giảm" if side == "down" else "cùng tăng", "corr_emp": c,
                         "n_obs": n, "corr_normal_implied": cn, "excess": c - cn, "corr_uncond": rho})
    return pd.DataFrame(rows)


def forbes_rigobon(returns: pd.DataFrame, cfg: dict, lagged: pd.DataFrame) -> pd.DataFrame:
    """Tương quan trong giai đoạn stress so với yên ổn, kèm hiệu chỉnh Forbes–Rigobon:
    ρ* = ρ_c / √(1 + δ(1 − ρ_c²)), δ = Var_c(S&P)/Var_yên ổn(S&P) − 1.
    Dùng dữ liệu lệch pha (S&P phiên t−1 với VN phiên t) để tránh chệch do lệch múi giờ."""
    from .config import stress_mask

    rows = []
    for lab, df in (("đồng thời", returns), ("lệch pha", lagged)):
        calm = df[~stress_mask(df.index, cfg)]
        rc = calm["VN"].corr(calm["SP_VND"])
        for k, p in enabled_periods(cfg).items():
            s = df.loc[p["start"]:p["end"]]
            rho = s["VN"].corr(s["SP_VND"])
            delta = s["SP_VND"].var() / calm["SP_VND"].var() - 1
            adj = rho / np.sqrt(1 + delta * (1 - rho**2))
            rows.append({"data": lab, "period": k, "corr_calm": rc, "corr_stress": rho, "delta_var": delta,
                         "corr_adjusted_FR": adj, "N": len(s)})
    return pd.DataFrame(rows)


def mt2_text(terc: pd.DataFrame, reg: pd.DataFrame, tail: pd.DataFrame, fr: pd.DataFrame) -> str:
    """Đoạn kết luận MT2 tự sinh (ngôn ngữ mô tả, không nhân quả)."""
    t = terc[(terc["corr_measure"] == "corr_252") & (terc["metric"] == "DR")]
    lo = t[t["tercile"] == "Thấp"]["mean"].iloc[0]
    hi = t[t["tercile"] == "Cao"]["mean"].iloc[0]
    diff = t[t["tercile"] == "Cao − Thấp"].iloc[0]
    r = reg[(reg["x"] == "corr_252") & (reg["y"] == "DR")].iloc[0]
    td = tail[(tail["q"] == 0.10) & (tail["side"] == "cùng giảm")].iloc[0]
    frl = fr[fr["data"] == "lệch pha"]
    return (
        f"- Lợi ích đa dạng hóa tương đối (DR) trung bình {100 * lo:.1f}% khi tương quan 252 phiên ở tam phân vị thấp, "
        f"so với {100 * hi:.1f}% ở tam phân vị cao (chênh {100 * diff['mean']:.1f} điểm %, p block bootstrap = "
        f"{diff['p_block_bootstrap']:.3f}) — T8_diversification_by_corr.\n"
        f"- Hồi quy mô tả DR theo ρ (Newey–West): b = {r['b']:.3f} (p = {r['p_b_NW']:.3f}); hệ số âm nghĩa là lợi ích "
        "đa dạng hóa **đi kèm với** mức thấp hơn khi tương quan cao hơn (không hàm ý nhân quả).\n"
        f"- Tương quan khi cả hai thị trường cùng giảm mạnh (10% đuôi) = {td['corr_emp']:.2f} so với "
        f"{td['corr_normal_implied']:.2f} nếu lợi suất là Normal cùng ρ — T8b_tail_correlation.\n"
        f"- Với dữ liệu lệch pha, tương quan trong các giai đoạn stress dao động {frl['corr_stress'].min():.2f}–"
        f"{frl['corr_stress'].max():.2f} (yên ổn {frl['corr_calm'].iloc[0]:.2f}); sau hiệu chỉnh Forbes–Rigobon còn "
        f"{frl['corr_adjusted_FR'].min():.2f}–{frl['corr_adjusted_FR'].max():.2f} — T8d_forbes_rigobon."
    )


def run(cfg: dict | None = None) -> str:
    from .portfolio import load_returns
    from .rolling import load_forecasts

    cfg = cfg or load_config()
    dc = cfg["diversification"]
    returns, lagged = load_returns(cfg), load_returns(cfg, lagged=True)
    corr, dcc_par = corr_timeseries(returns, lagged, cfg)
    fc = load_forecasts(cfg, "main")
    frames, terc, regs = [], [], []
    for model in cfg["models_main"]:
        db = diversification_benefit(fc, model).join(corr, how="left")
        db["model"] = model
        frames.append(db)
        for cc in ("corr_252", "corr_63", "corr_dcc", "corr_lag_252", "corr_dcc_lag"):
            terc.append(tercile_analysis(db, cc, cfg).assign(model=model))
            regs.append(nw_regression(db, cc) | {"model": model})
    ts = pd.concat(frames)
    ts.to_parquet(path_of("processed", cfg) / "diversification_timeseries.parquet")
    corr.to_parquet(path_of("processed", cfg) / "correlations.parquet")
    terc, reg = pd.concat(terc, ignore_index=True), pd.DataFrame(regs)
    tail = tail_correlation(lagged["VN"], lagged["SP_VND"], dc["tail_quantiles"], cfg["seed"])
    fr = forbes_rigobon(returns, cfg, lagged)
    save_table(terc, "T8_diversification_by_corr")
    save_table(reg, "T8a_dr_regression_nw")
    save_table(tail, "T8b_tail_correlation")
    save_table(pd.DataFrame(dcc_par), "T8c_dcc_params")
    save_table(fr, "T8d_forbes_rigobon")
    neg = (ts["DR"] < -1e-9).mean()
    if neg > 0:
        log.warning("DR âm ở %.2f%% số ngày — kiểm tra (ES ước lượng không nhất thiết dưới cộng tính trên mẫu hữu hạn)", 100 * neg)
    prim = terc[terc["model"] == dc["primary_model"]]
    return mt2_text(prim, reg[reg["model"] == dc["primary_model"]], tail, fr)
