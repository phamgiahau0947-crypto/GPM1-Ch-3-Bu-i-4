"""Phương pháp tham số Normal.

Tài liệu: Jorion (2006, ch. 5); Acerbi & Tasche (2002).
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np
from scipy import stats

from ._common import DEFAULT_ES, DEFAULT_VAR, location_scale_result, normal_es


def forecast_normal(returns_window: np.ndarray, var_levels: Sequence[float] = DEFAULT_VAR,
                    es_level: float = DEFAULT_ES, **kw) -> dict:
    """Variance–covariance (Normal).

    VaR_q = −(μ + σ z_{1−q}),   ES_q = −μ + σ φ(z_q)/(1 − q)
    μ, σ ước lượng bằng trung bình và độ lệch chuẩn mẫu (ddof = 1) của cửa sổ.
    Giả định: r ~ N(μ, σ²) i.i.d. — bỏ qua đuôi dày và biến động theo cụm.
    """
    r = np.asarray(returns_window, dtype=float)
    return location_scale_result(r.mean(), r.std(ddof=1), stats.norm.ppf, normal_es,
                                 var_levels, es_level, {})
