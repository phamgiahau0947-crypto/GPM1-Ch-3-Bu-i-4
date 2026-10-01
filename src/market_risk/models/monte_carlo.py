"""Mô phỏng Monte Carlo dưới giả định Normal.

Tài liệu: Jorion (2006, ch. 12). N = 10.000 đường, seed cố định → tái lập tuyệt đối.
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from ._common import DEFAULT_ES, DEFAULT_VAR, empirical_result


def forecast_mc(returns_window: np.ndarray, var_levels: Sequence[float] = DEFAULT_VAR,
                es_level: float = DEFAULT_ES, n_paths: int = 10_000, seed: int = 2026,
                **kw) -> dict:
    """Monte Carlo 1 ngày: mô phỏng r̃_j = μ̂ + σ̂ z_j, j = 1..N, rồi lấy VaR/ES thực nghiệm của mẫu mô phỏng.

    z ~ N(0,1). Cùng seed ⇒ cùng kết quả (dùng ``numpy.random.default_rng(seed)``).
    Sai số Monte Carlo của VaR 99% với N = 10.000 là nhỏ nhưng khác 0 so với công thức đóng.
    """
    r = np.asarray(returns_window, dtype=float)
    mu, sd = r.mean(), r.std(ddof=1)
    rng = np.random.default_rng(seed)
    params = {"mu": mu, "sigma": sd, "n_paths": n_paths, "dist": "normal"}
    z = rng.standard_normal(n_paths)
    return empirical_result(mu + sd * z, var_levels, es_level, params)
