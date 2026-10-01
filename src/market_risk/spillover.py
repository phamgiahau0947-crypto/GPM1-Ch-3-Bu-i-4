"""Mở rộng theo Bài 9 — Mô hình VAR (Vector Autoregression) cho VN–S&P–tỷ giá (MT2, MT3, mô tả).

Quy trình: (1) chọn độ trễ theo AIC/BIC/HQ; (2) ước lượng VAR(p), kiểm tra tính ổn định (nghiệm);
(3) kiểm định nhân quả Granger; (4) hàm phản ứng xung trực giao (IRF) và phân rã phương sai (FEVD).

    Y_t = c + A_1 Y_{t−1} + … + A_p Y_{t−p} + ε_t,   Y = (r_SP_USD, r_USDVND, r_VN)'

Thứ tự Cholesky: S&P (thị trường toàn cầu) → tỷ giá → VN-Index. Vì phiên Mỹ ngày t đóng cửa SAU phiên
VN ngày t, tác động S&P → VN chủ yếu xuất hiện ở độ trễ 1. Granger causality chỉ là "dự báo được",
không phải nhân quả kinh tế (Granger 1969; Sims 1980).
"""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd
from statsmodels.tsa.api import VAR

from .config import load_config, path_of, save_table, stars

log = logging.getLogger(__name__)
ORDER = ["SP_USD", "USDVND", "VN"]
LABEL = {"SP_USD": "S&P 500", "USDVND": "USD/VND", "VN": "VN-Index"}


def run(cfg: dict | None = None) -> str:
    from .portfolio import load_returns

    cfg = cfg or load_config()
    vc = cfg["var_model"]
    y = load_returns(cfg)[ORDER] * 100
    model = VAR(y)
    sel = model.select_order(vc["maxlags"])
    lag_tab = pd.DataFrame({"criterion": ["AIC", "BIC", "HQIC", "FPE"],
                            "selected_lag": [sel.aic, sel.bic, sel.hqic, sel.fpe]})
    p = max(int(sel.bic), 1)
    res = model.fit(p)
    rows = []
    for cause in ORDER:
        for effect in ORDER:
            if cause == effect:
                continue
            t = res.test_causality(effect, [cause], kind="f")
            rows.append({"cause": LABEL[cause], "effect": LABEL[effect], "lag_p": p, "F": t.test_statistic,
                         "p_value": t.pvalue, "sig": stars(t.pvalue),
                         "conclusion": (f"{LABEL[cause]} Granger-gây ra {LABEL[effect]} (có thông tin dự báo)"
                                        if t.pvalue < 0.05 else "Không có quan hệ Granger ở mức 5%")})
    gr = pd.DataFrame(rows)
    fevd = res.fevd(vc["irf_horizon"])
    fe_rows = []
    for i, v in enumerate(ORDER):
        dec = fevd.decomp[i][-1]
        fe_rows.append({"variable": LABEL[v], **{f"share_{LABEL[s]}": 100 * dec[j] for j, s in enumerate(ORDER)}})
    irf = res.irf(vc["irf_horizon"])
    np.save(path_of("processed", cfg) / "var_irf_orth.npy", irf.orth_irfs)
    stable = bool(res.is_stable())
    lag_tab["estimated_lag"] = p
    lag_tab["stable"] = stable
    save_table(lag_tab, "T16_var_lag_selection")
    save_table(gr, "T16_var_granger")
    save_table(pd.DataFrame(fe_rows), "T16_var_fevd")
    sp_vn = gr[(gr["cause"] == "S&P 500") & (gr["effect"] == "VN-Index")].iloc[0]
    fx_vn = gr[(gr["cause"] == "USD/VND") & (gr["effect"] == "VN-Index")].iloc[0]
    vn_share = fe_rows[2]
    return (f"- VAR({p}) chọn theo BIC, mô hình ổn định = {stable}. S&P 500 → VN-Index: F = {sp_vn['F']:.1f}, "
            f"p = {sp_vn['p_value']:.3g}; USD/VND → VN-Index: p = {fx_vn['p_value']:.3g} — T16_var_granger.\n"
            f"- Sau {vc['irf_horizon']} ngày, cú sốc S&P giải thích {vn_share['share_S&P 500']:.1f}% và tỷ giá "
            f"{vn_share['share_USD/VND']:.1f}% phương sai sai số dự báo của VN-Index — T16_var_fevd.")
