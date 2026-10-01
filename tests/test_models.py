"""Phase 3: công thức VaR/ES với giá trị biết trước."""
import numpy as np
import pytest
from arch.univariate import GARCH, ConstantMean, Normal
from scipy import stats

from market_risk.models import MODELS
from market_risk.models._common import location_scale_result, normal_es
from market_risk.models.garch import filter_variance, fit_garch
from market_risk.models.historical import forecast_hs


def test_registry_contains_only_required_models():
    assert list(MODELS) == ["HS", "Normal", "MC_Normal", "GARCH_N"]


def test_normal_closed_form():
    o = location_scale_result(0.0, 1.0, stats.norm.ppf, normal_es, (0.95, 0.99), 0.975, {})
    assert abs(o["VaR_99"] - 2.3263) < 1e-3
    assert abs(o["VaR_95"] - 1.6449) < 1e-3
    assert abs(o["ES_975"] - 2.3378) < 1e-3


def test_hs_on_known_sample():
    r = -np.arange(1, 201) / 100.0            # lỗ 0,01 .. 2,00
    o = forecast_hs(r, (0.99,), 0.975)
    assert abs(o["VaR_99"] - (-np.quantile(r, 0.01))) < 1e-12
    thr = np.quantile(r, 0.025)
    assert abs(o["ES_975"] - (-r[r <= thr].mean())) < 1e-12


@pytest.mark.parametrize("model", list(MODELS))
def test_es_ge_var_same_level(model):
    rng = np.random.default_rng(1)
    r = stats.t.rvs(4, size=1000, random_state=rng) * 0.01
    o = MODELS[model](r)
    assert o["ES_975"] >= o["VaR_975"] - 1e-10
    assert o["VaR_99"] >= o["VaR_95"] - 1e-10


def test_monte_carlo_reproducible():
    r = np.random.default_rng(3).normal(0, 0.01, 500)
    a, b = MODELS["MC_Normal"](r), MODELS["MC_Normal"](r)
    assert a["VaR_99"] == b["VaR_99"] and a["ES_975"] == b["ES_975"]


def test_garch_recovers_known_parameters():
    # Mô phỏng GARCH(1,1) với tham số biết trước (thang %): μ = 0,05; ω = 0,05; α = 0,08; β = 0,90
    sim = ConstantMean(None, volatility=GARCH(), distribution=Normal(seed=np.random.default_rng(2026)))
    sim_data = sim.simulate(np.array([0.05, 0.05, 0.08, 0.90]), 6000, burn=500)
    fit, _ = fit_garch(sim_data["data"].values / 100)
    for est, tv in ((fit.omega, 0.05), (fit.alpha, 0.08), (fit.beta, 0.90)):
        assert abs(est / tv - 1) < 0.20, (est, tv)


def test_filter_variance_matches_arch():
    sim = ConstantMean(None, volatility=GARCH(), distribution=Normal(seed=np.random.default_rng(5)))
    r = sim.simulate(np.array([0.05, 0.05, 0.06, 0.88]), 1500)["data"].values / 100
    fit, res = fit_garch(r)
    s2 = filter_variance(r, fit)
    assert np.allclose(np.sqrt(s2[:-1]), res.conditional_volatility, rtol=1e-6)
