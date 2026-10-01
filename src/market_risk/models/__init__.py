"""Bốn phương pháp VaR/ES thuộc phạm vi đề án.

    forecast(returns_window, var_levels=(0.95, 0.975, 0.99), es_level=0.975, **kw) -> dict
    # {"VaR_95", "VaR_975", "VaR_99", "ES_975", "params": {...}}  — số dương = mức lỗ

HS, Normal, MC_Normal và GARCH_N lần lượt là mô phỏng lịch sử, tham số chuẩn,
Monte Carlo chuẩn và GARCH(1,1) với đổi mới chuẩn.
"""

from functools import partial

from .garch import forecast_garch
from .historical import forecast_hs
from .monte_carlo import forecast_mc
from .parametric import forecast_normal

MODELS = {
    "HS": forecast_hs,
    "Normal": forecast_normal,
    "MC_Normal": partial(forecast_mc, dist="normal"),
    "GARCH_N": forecast_garch,
}

MODEL_LABELS = {
    "HS": "Mô phỏng lịch sử (HS)",
    "Normal": "Phương pháp tham số (Normal)",
    "MC_Normal": "Monte Carlo (MC_Normal)",
    "GARCH_N": "GARCH(1,1) (GARCH_N)",
}

MODEL_TIER = {name: "Theo đề" for name in MODELS}
GARCH_BASED = {"GARCH_N"}
