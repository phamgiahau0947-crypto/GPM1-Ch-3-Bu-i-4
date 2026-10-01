"""Mô hình biến động có điều kiện GARCH(1,1) với đổi mới Normal.

Tài liệu: Engle (1982); Bollerslev (1986).

    r_t = μ + ε_t,  ε_t = σ_t z_t,  z_t ~ N(0, 1)
    σ²_t = ω + α ε²_{t−1} + β σ²_{t−1}
"""

from __future__ import annotations

import warnings
from collections.abc import Sequence
from dataclasses import dataclass

import numpy as np
from arch import arch_model
from scipy import signal, stats

from ._common import DEFAULT_ES, DEFAULT_VAR, location_scale_result, normal_es

SCALE = 100.0


@dataclass
class GarchFit:
    """Tham số GARCH(1,1) ở thang lợi suất × 100."""

    mu: float
    omega: float
    alpha: float
    beta: float
    loglik: float = np.nan
    converged: bool = True

    @property
    def persistence(self) -> float:
        return self.alpha + self.beta


def fit_garch(returns: np.ndarray, start: GarchFit | None = None):
    """Ước lượng GARCH(1,1)-Normal bằng MLE, trả về tham số và kết quả ``arch``."""
    am = arch_model(np.asarray(returns) * SCALE, mean="Constant", vol="GARCH", p=1, o=0, q=1,
                    dist="normal", rescale=False)
    sv = [start.mu, start.omega, start.alpha, start.beta] if start is not None and start.converged else None
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        res = am.fit(disp="off", starting_values=sv, options={"maxiter": 500})
    p = res.params
    fit = GarchFit(mu=p["mu"], omega=p["omega"], alpha=p["alpha[1]"], beta=p["beta[1]"],
                   loglik=res.loglikelihood)
    fit.converged = bool(res.convergence_flag == 0 and fit.persistence < 1.0 and fit.omega > 0)
    return fit, res


def backcast(eps: np.ndarray, tau: int = 75) -> float:
    """Giá trị khởi tạo σ²_0 như thư viện arch: trọng số 0,94^i cho ε² đầu chuỗi."""
    tau = min(tau, len(eps))
    w = 0.94 ** np.arange(tau)
    return float(np.sum(w / w.sum() * eps[:tau] ** 2))


def filter_variance(returns: np.ndarray, fit: GarchFit) -> np.ndarray:
    """Đệ quy σ² trên cửa sổ; phần tử cuối là dự báo σ²_{T+1}."""
    y = np.asarray(returns) * SCALE
    eps = y - fit.mu
    shock = fit.omega + fit.alpha * eps**2
    bc = backcast(y - y.mean())
    s2_1 = fit.omega + (fit.alpha + fit.beta) * bc
    return signal.lfilter([1.0], [1.0, -fit.beta], np.concatenate([[s2_1], shock]))


def garch_forecast_from_fit(returns: np.ndarray, fit: GarchFit, var_levels: Sequence[float],
                            es_level: float) -> dict:
    """VaR/ES 1 ngày từ tham số GARCH(1,1)-Normal đã ước lượng."""
    s2 = filter_variance(returns, fit)
    return location_scale_result(fit.mu / SCALE, np.sqrt(s2[-1]) / SCALE,
                                 stats.norm.ppf, normal_es, var_levels, es_level,
                                 {"persistence": fit.persistence})


def forecast_garch(returns_window: np.ndarray, var_levels: Sequence[float] = DEFAULT_VAR,
                   es_level: float = DEFAULT_ES, fit: GarchFit | None = None, **kw) -> dict:
    """Ước lượng (nếu chưa có ``fit``) rồi dự báo VaR/ES ngày tiếp theo."""
    if fit is None:
        fit, _ = fit_garch(returns_window)
    return garch_forecast_from_fit(returns_window, fit, var_levels, es_level)
