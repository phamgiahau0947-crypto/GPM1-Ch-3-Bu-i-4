"""Kiểm định giả định: dữ liệu chuẩn i.i.d. không bị bác bỏ, dữ liệu có cụm biến động thì có hiệu ứng ARCH."""

import numpy as np
import pandas as pd

from market_risk.descriptive import assumption_tests


def _p(rows: list[dict], test: str) -> float:
    return next(r["p_value"] for r in rows if r["test"] == test)


def test_assumption_tests_iid_normal_not_rejected():
    r = pd.Series(np.random.default_rng(2026).normal(0, 0.01, 3000))
    rows = assumption_tests("VN", r)
    assert len(rows) == 8
    assert _p(rows, "Jarque–Bera") > 0.05
    assert _p(rows, "ARCH-LM(10)") > 0.05
    assert _p(rows, "ADF") < 0.05


def test_assumption_tests_detects_volatility_clustering():
    rng = np.random.default_rng(2026)
    z, s2, eps = rng.standard_normal(3000), np.empty(3000), np.empty(3000)
    s2[0] = 1e-4
    for t in range(3000):                       # GARCH(1,1): ω = 2e-6, α = 0,10, β = 0,88
        if t:
            s2[t] = 2e-6 + 0.10 * eps[t - 1] ** 2 + 0.88 * s2[t - 1]
        eps[t] = np.sqrt(s2[t]) * z[t]
    rows = assumption_tests("VN", pd.Series(eps))
    assert _p(rows, "ARCH-LM(10)") < 0.01
    assert _p(rows, "Jarque–Bera") < 0.01          # GARCH tạo đuôi dày dù đổi mới chuẩn
