"""Phase 4: chống look-ahead — thay r[t+1] bằng giá trị cực đoan thì dự báo lập tại t không đổi."""
import numpy as np
import pytest

from market_risk.rolling import rolling_forecast


@pytest.mark.parametrize("model", ["HS", "Normal", "MC_Normal", "GARCH_N"])
def test_no_lookahead(model):
    rng = np.random.default_rng(11)
    r = rng.standard_t(5, 420) * 0.01
    a, _ = rolling_forecast(r, model, 252, 20)
    t0 = 350
    r2 = r.copy()
    r2[t0 + 1] = -0.9                                   # cú sốc cực đoan tại ngày t0+1
    b, _ = rolling_forecast(r2, model, 252, 20)
    assert np.allclose(a[: t0 + 2], b[: t0 + 2], equal_nan=True)   # mọi dự báo lập đến ngày t0 giữ nguyên
    assert not np.allclose(a[t0 + 2], b[t0 + 2])                   # dự báo lập tại t0+1 thì thay đổi


def test_forecast_alignment():
    r = np.arange(300, dtype=float) / 1000 - 0.15
    a, _ = rolling_forecast(r, "HS", 252, 20)
    assert np.isnan(a[:252]).all() and not np.isnan(a[252, :4]).any()
    assert np.isclose(a[252, 2], -np.quantile(r[0:252], 0.01))
