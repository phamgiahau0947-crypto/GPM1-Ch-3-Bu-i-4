"""Tiện ích chung cho các mô hình VaR/ES.

Quy ước dấu: VaR và ES là **số dương = mức lỗ** (CLAUDE.md §4).
Với lợi suất r có phân phối dự báo F, mức tin cậy q (vd. 0,99):

    VaR_q = −F^{-1}(1 − q)
    ES_q  = −E[r | r ≤ F^{-1}(1 − q)] = −(1/(1−q)) ∫_0^{1−q} F^{-1}(u) du
"""

from __future__ import annotations

from collections.abc import Callable, Sequence

import numpy as np
from scipy import stats

DEFAULT_VAR = (0.95, 0.975, 0.99)
DEFAULT_ES = 0.975

# Nút Gauss–Legendre cho tích phân ES (đổi biến u = p·v² làm mềm điểm kỳ dị tại u → 0)
_GL_X, _GL_W = np.polynomial.legendre.leggauss(200)


def level_key(prefix: str, q: float) -> str:
    """0.95 → 'VaR_95', 0.975 → 'VaR_975', 0.99 → 'VaR_99'."""
    return f"{prefix}_{str(round(q * 100, 1)).rstrip('0').rstrip('.').replace('.', '')}"


def es_from_ppf(ppf: Callable[[np.ndarray], np.ndarray], q: float) -> float:
    """ES_q của biến chuẩn hóa từ hàm phân vị: −(1/p)∫_0^p Q(u) du, p = 1 − q (dấu dương = lỗ)."""
    p = 1.0 - q
    v = 0.5 * (_GL_X + 1.0)                  # v ∈ (0, 1)
    u = p * v**2
    integral = np.sum(0.5 * _GL_W * ppf(u) * 2.0 * p * v)
    return float(-integral / p)


# ---------------------------------------------------------------------------
# Phân phối chuẩn hóa (trung bình 0, phương sai 1)
# ---------------------------------------------------------------------------
def std_t_ppf(u: np.ndarray | float, nu: float) -> np.ndarray:
    """Phân vị của Student-t chuẩn hóa phương sai 1: t_ν^{-1}(u)·√((ν−2)/ν)."""
    return stats.t.ppf(u, nu) * np.sqrt((nu - 2.0) / nu)


def std_t_es(q: float, nu: float) -> float:
    """ES đóng của Student-t chuẩn hóa (dấu dương = lỗ).

    ES = [(ν + t_p²)/(ν − 1)] · f_ν(t_p)/p · √((ν−2)/ν),  với t_p = t_ν^{-1}(p), p = 1 − q.
    """
    p = 1.0 - q
    tp = stats.t.ppf(p, nu)
    return float((nu + tp**2) / (nu - 1.0) * stats.t.pdf(tp, nu) / p * np.sqrt((nu - 2.0) / nu))


def normal_es(q: float) -> float:
    """ES của N(0,1): φ(z_q)/(1 − q)."""
    return float(stats.norm.pdf(stats.norm.ppf(q)) / (1.0 - q))


def location_scale_result(mu: float, sigma: float, ppf: Callable, es_std: Callable[[float], float],
                          var_levels: Sequence[float], es_level: float, params: dict) -> dict:
    """Ghép kết quả cho mô hình vị trí–tỷ lệ r = μ + σ·z: VaR = −(μ + σ Q_z(1−q)), ES = −μ + σ ES_z."""
    out = {level_key("VaR", q): float(-(mu + sigma * ppf(1.0 - q))) for q in var_levels}
    out[level_key("ES", es_level)] = float(-mu + sigma * es_std(es_level))
    out["params"] = {"mu": mu, "sigma": sigma, **params}
    return out


def empirical_result(sample: np.ndarray, var_levels: Sequence[float], es_level: float,
                     params: dict | None = None) -> dict:
    """VaR/ES từ một mẫu lợi suất (mô phỏng hoặc lịch sử), phân vị nội suy tuyến tính (Hyndman–Fan loại 7)."""
    out = {level_key("VaR", q): float(-np.quantile(sample, 1.0 - q)) for q in var_levels}
    thr = np.quantile(sample, 1.0 - es_level)
    out[level_key("ES", es_level)] = float(-sample[sample <= thr].mean())
    out["params"] = params or {}
    return out
