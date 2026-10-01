"""Thống kê mô tả (T1) và kiểm định giả định của các mô hình VaR (T2).

Kiểm định giả định trả lời: lợi suất có chuẩn không (giả định của Normal, MC_Normal), có dừng không (điều kiện
để mô hình hóa trên lợi suất), có biến động theo cụm không (lý do cần GARCH(1,1)).
Tài liệu: Jarque & Bera (1980); Dickey & Fuller (1979); Kwiatkowski et al. (1992); Engle (1982); Ljung & Box (1978).
"""

from __future__ import annotations

import warnings

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.diagnostic import acorr_ljungbox, het_arch, normal_ad
from statsmodels.tools.sm_exceptions import InterpolationWarning
from statsmodels.tsa.stattools import adfuller, kpss

from .config import enabled_periods, load_config, save_table, stars

# statsmodels 0.15 báo trước việc đổi kiểu trả về của các hàm này (không ảnh hưởng kết quả)
warnings.filterwarnings("ignore", category=FutureWarning, message=".*(adfuller|kpss|acorr_lm) currently returns")

SERIES_LABEL = {
    "VN": "VN-Index", "SP_USD": "S&P 500 (USD)", "SP_VND": "S&P 500 (VND)",
    "USDVND": "USD/VND", "VN100": "DM 100% VN", "VN50_SP50": "DM 50/50", "SP100": "DM 100% S&P",
}
DESCRIPTIVE_SERIES = ["VN", "SP_USD", "SP_VND", "USDVND", "VN50_SP50"]


def describe(returns: pd.Series) -> dict:
    """Thống kê mô tả; độ lệch chuẩn và trung bình được năm hóa theo 252 phiên."""
    return {
        "N": returns.size,
        "mean": returns.mean(),
        "std": returns.std(),
        "mean_ann": returns.mean() * 252,
        "std_ann": returns.std() * np.sqrt(252),
        "min": returns.min(),
        "max": returns.max(),
        "skew": stats.skew(returns),
        "exkurt": stats.kurtosis(returns),
        "q01": returns.quantile(0.01),
        "q025": returns.quantile(0.025),
        "q05": returns.quantile(0.05),
    }


def descriptive_table(returns: pd.DataFrame, columns: list[str], cfg: dict) -> pd.DataFrame:
    """T1: thống kê mô tả toàn kỳ và từng giai đoạn stress."""
    periods = {"Toàn kỳ": (None, None)} | {
        key: (value["start"], value["end"]) for key, value in enabled_periods(cfg).items()
    }
    rows = []
    for period, (start, end) in periods.items():
        sample = returns.loc[start:end] if start else returns
        for column in columns:
            rows.append({
                "period": period,
                "series": column,
                "label": SERIES_LABEL.get(column, column),
                **describe(sample[column]),
            })
    return pd.DataFrame(rows)


def _row(series: str, test: str, stat: float, p: float, conclusion: str) -> dict:
    return {"series": series, "label": SERIES_LABEL.get(series, series), "test": test, "statistic": stat,
            "p_value": p, "sig": stars(p), "conclusion": conclusion}


def assumption_tests(name: str, r: pd.Series) -> list[dict]:
    """Chuẩn (Jarque–Bera, Anderson–Darling), dừng (ADF: H0 nghiệm đơn vị; KPSS: H0 dừng), ARCH-LM(5, 10) và
    Ljung–Box Q(10) trên r và r² (tự tương quan lợi suất / cụm biến động)."""
    x = r.dropna()
    e = x - x.mean()
    jb = stats.jarque_bera(x)
    ad, p_ad = normal_ad(x.values)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", InterpolationWarning)     # p-value KPSS bị chặn trong [0,01; 0,10]
        adf = adfuller(x.values, autolag="AIC")
        kp = kpss(x.values, regression="c", nlags="auto")
    rows = [
        _row(name, "Jarque–Bera", jb.statistic, jb.pvalue,
             "Bác bỏ phân phối chuẩn → Normal/MC_Normal dễ đánh giá thấp rủi ro đuôi" if jb.pvalue < 0.05
             else "Chưa bác bỏ phân phối chuẩn"),
        _row(name, "Anderson–Darling", ad, p_ad, "Bác bỏ chuẩn" if p_ad < 0.05 else "Chưa bác bỏ chuẩn"),
        _row(name, "ADF", adf[0], adf[1], "Bác bỏ nghiệm đơn vị → dừng" if adf[1] < 0.05 else "Không bác bỏ nghiệm đơn vị"),
        _row(name, "KPSS", kp[0], kp[1], "Bác bỏ tính dừng" if kp[1] < 0.05 else "Không bác bỏ tính dừng"),
    ]
    for lag in (5, 10):
        lm, p, _, _ = het_arch(e.values, nlags=lag)
        rows.append(_row(name, f"ARCH-LM({lag})", lm, p,
                         "Có hiệu ứng ARCH (biến động theo cụm) → cần GARCH" if p < 0.05 else "Không thấy hiệu ứng ARCH"))
    for lab, y in (("r", e), ("r²", e**2)):
        lb = acorr_ljungbox(y.values, lags=[10])
        p = float(lb["lb_pvalue"].iloc[0])
        what = "tự tương quan trong lợi suất" if lab == "r" else "tự tương quan trong r² (cụm biến động)"
        rows.append(_row(name, f"Ljung–Box Q(10) {lab}", float(lb["lb_stat"].iloc[0]), p,
                         f"Có {what}" if p < 0.05 else f"Không có {what}"))
    return rows


def summary_text(t2: pd.DataFrame) -> str:
    """Đoạn tổng kết tự sinh cho phần kiểm định giả định."""
    def n_reject(test: str) -> int:
        return int((t2.loc[t2["test"] == test, "p_value"] < 0.05).sum())

    k = t2["series"].nunique()
    return (f"- Jarque–Bera bác bỏ phân phối chuẩn ở {n_reject('Jarque–Bera')}/{k} chuỗi → giả định chuẩn của Normal và "
            "MC_Normal không được dữ liệu ủng hộ; HS (không giả định phân phối) là mô hình đối chứng.\n"
            f"- ARCH-LM(10) có ý nghĩa ở {n_reject('ARCH-LM(10)')}/{k} chuỗi và Ljung–Box trên r² ở "
            f"{n_reject('Ljung–Box Q(10) r²')}/{k} chuỗi → biến động theo cụm, là căn cứ dùng GARCH(1,1).\n"
            f"- ADF bác bỏ nghiệm đơn vị ở {n_reject('ADF')}/{k} chuỗi lợi suất (KPSS không bác bỏ tính dừng ở "
            f"{k - n_reject('KPSS')}/{k}) → mô hình hóa trên lợi suất là phù hợp.")


def run(returns: pd.DataFrame | None = None, cfg: dict | None = None) -> str:
    """Xuất T1 (mô tả) và T2 (kiểm định giả định); trả về đoạn tổng kết."""
    from .portfolio import load_returns

    cfg = cfg or load_config()
    returns = returns if returns is not None else load_returns(cfg)
    save_table(descriptive_table(returns, DESCRIPTIVE_SERIES + ["VN100", "SP100"], cfg), "T1_descriptive")
    t2 = pd.DataFrame([row for c in DESCRIPTIVE_SERIES for row in assumption_tests(c, returns[c])])
    save_table(t2, "T2_assumption_tests")
    return summary_text(t2)
