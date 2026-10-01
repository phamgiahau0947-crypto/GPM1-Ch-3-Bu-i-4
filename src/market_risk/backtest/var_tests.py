"""Kupiec (1995) và Christoffersen (1998) backtests cho chuỗi vi phạm VaR."""

from __future__ import annotations

import numpy as np
from scipy import stats
from scipy.special import xlogy


def _ll_bernoulli(n0: float, n1: float, pi: float) -> float:
    """Log-likelihood Bernoulli với quy ước 0·ln 0 = 0."""
    return float(xlogy(n0, 1 - pi) + xlogy(n1, pi))


def kupiec(hits: np.ndarray, p: float) -> dict:
    """Kupiec POF kiểm định tỷ lệ vi phạm quan sát so với mức danh nghĩa p."""
    hits = np.asarray(hits, dtype=int)
    T, x = hits.size, int(hits.sum())
    if T == 0:
        return {"T": 0, "x": 0, "expected": 0.0, "rate": np.nan, "LR_uc": np.nan, "p_uc": np.nan}
    lr = -2 * _ll_bernoulli(T - x, x, p) + 2 * _ll_bernoulli(T - x, x, x / T)
    lr = max(lr, 0.0)
    return {"T": T, "x": x, "expected": p * T, "rate": x / T, "LR_uc": lr,
            "p_uc": float(stats.chi2.sf(lr, 1))}


def transition_counts(hits: np.ndarray) -> tuple[int, int, int, int]:
    """Đếm chuyển trạng thái n_ij = #{I_{t−1} = i, I_t = j}."""
    h = np.asarray(hits, dtype=int)
    a, b = h[:-1], h[1:]
    return (int(((a == 0) & (b == 0)).sum()), int(((a == 0) & (b == 1)).sum()),
            int(((a == 1) & (b == 0)).sum()), int(((a == 1) & (b == 1)).sum()))


def christoffersen(hits: np.ndarray, p: float) -> dict:
    """Christoffersen: kiểm định độc lập LR_ind và bao phủ có điều kiện LR_cc."""
    n00, n01, n10, n11 = transition_counts(hits)
    uc = kupiec(hits, p)
    n_transitions = n00 + n01 + n10 + n11
    if n_transitions == 0:
        return {**uc, "n00": n00, "n01": n01, "n10": n10, "n11": n11, "pi01": 0.0, "pi11": 0.0,
                "LR_ind": np.nan, "p_ind": np.nan, "LR_cc": np.nan, "p_cc": np.nan}
    pi01 = n01 / (n00 + n01) if n00 + n01 else 0.0
    pi11 = n11 / (n10 + n11) if n10 + n11 else 0.0
    pi = (n01 + n11) / n_transitions
    l0 = _ll_bernoulli(n00 + n10, n01 + n11, pi)
    l1 = _ll_bernoulli(n00, n01, pi01) + _ll_bernoulli(n10, n11, pi11)
    lr_ind = max(-2 * (l0 - l1), 0.0)
    lr_cc = uc["LR_uc"] + lr_ind
    return {**uc, "n00": n00, "n01": n01, "n10": n10, "n11": n11, "pi01": pi01, "pi11": pi11,
            "LR_ind": lr_ind, "p_ind": float(stats.chi2.sf(lr_ind, 1)),
            "LR_cc": lr_cc, "p_cc": float(stats.chi2.sf(lr_cc, 2))}
