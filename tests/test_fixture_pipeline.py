"""Smoke test trên dữ liệu mẫu nhỏ (tests/fixtures) — chạy được trong CI không cần dữ liệu đầy đủ."""
from pathlib import Path

import numpy as np
import pandas as pd

from market_risk.backtest.var_tests import christoffersen
from market_risk.portfolio import asset_returns, build_portfolios
from market_risk.rolling import rolling_forecast

FIX = Path(__file__).parent / "fixtures" / "sample_prices.csv"


def test_fixture_end_to_end():
    prices = pd.read_csv(FIX, index_col="Date", parse_dates=True)
    assert prices.index.is_monotonic_increasing
    r = asset_returns(prices)
    p = build_portfolios(r, {"VN50_SP50": [0.5, 0.5]})["VN50_SP50"].values
    out, _ = rolling_forecast(p, "HS", 252, 20)
    ok = ~np.isnan(out[:, 2])
    hits = (p[ok] < -out[ok, 2]).astype(int)
    res = christoffersen(hits, 0.01)
    assert res["T"] == ok.sum() and 0 <= res["p_cc"] <= 1
    assert (out[ok, 3] >= out[ok, 1] - 1e-12).all()        # ES97,5 ≥ VaR97,5
