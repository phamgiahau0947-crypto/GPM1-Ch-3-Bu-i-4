"""Kiểm tra nguồn dữ liệu clean duy nhất và các quy tắc toàn vẹn chuỗi."""

import pandas as pd
import pytest

from market_risk.config import load_config
from market_risk.data_pipeline import _read_clean_prices, clean_fx_spikes, fred_sp500_check, merge_lagged, validate
from scripts.verify_reproducibility import data_manifest


def test_manifest_contains_only_the_two_pj4_clean_files():
    cfg = load_config()
    assert cfg["cleaned_files"]["directory"] == "data/clean"
    assert set(data_manifest(cfg)) == {
        "data/clean/cleaned_daily_data.csv",
        "data/clean/cleaned_cpi_inflation.csv",
    }


def test_clean_price_file_loads_expected_series_and_date_range():
    prices = _read_clean_prices(load_config())
    assert list(prices.columns) == ["VN", "SP_USD", "USDVND"]
    assert len(prices) == 4610
    assert prices.index.min() == pd.Timestamp("2006-02-07")
    assert prices.index.max() == pd.Timestamp("2025-02-28")
    assert prices.index.is_monotonic_increasing and not prices.index.duplicated().any()


def test_validate_rejects_invalid_price_series():
    index = pd.to_datetime(["2020-01-02", "2020-01-01"])
    with pytest.raises(ValueError, match="ngày không tăng dần"):
        validate(pd.Series([1.0, 2.0], index=index, name="VN"))

    duplicate_index = pd.to_datetime(["2020-01-01", "2020-01-01"])
    with pytest.raises(ValueError, match="có ngày trùng"):
        validate(pd.Series([1.0, 2.0], index=duplicate_index, name="VN"))

    with pytest.raises(ValueError, match="giá không dương"):
        validate(pd.Series([1.0, 0.0], index=pd.date_range("2020-01-01", periods=2), name="VN"))


def test_merge_lagged_uses_previous_us_close():
    dates = pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06"])
    vn = pd.Series([10, 11, 12.0], index=dates)
    sp = pd.Series([100, 101, 102.0], index=dates)
    fx = pd.Series([1, 1, 1.0], index=dates)
    out = merge_lagged(vn, sp, fx)
    assert out.loc["2020-01-03", "SP_USD"] == 100
    assert out.loc["2020-01-06", "SP_USD"] == 101


def test_clean_fx_spikes_removes_reversal_keeps_devaluation():
    # 01/12/2009-like spike (lệch rồi quay về) bị lọc; bước nhảy giữ mức mới (phá giá thật) được giữ lại
    vals = [18000.0] * 10 + [18900.0] + [18000.0] * 10 + [19000.0] * 12
    s = pd.Series(vals, index=pd.bdate_range("2009-11-02", periods=len(vals)), name="USDVND")
    clean, log = clean_fx_spikes(s)
    assert len(log) == 1 and log["value"].iloc[0] == 18900.0
    assert clean.iloc[10] == 18000.0
    assert clean.iloc[-1] == 19000.0 and clean.iloc[21] == 19000.0


def test_fred_sp500_check_matches_and_skips_missing(tmp_path):
    f = tmp_path / "SP500.csv"
    f.write_text("observation_date,SP500\n2020-01-02,100\n2020-01-03,.\n2020-01-06,102\n2020-01-07,103\n", encoding="utf-8")
    sp = pd.Series([100.0, 101.0, 102.051, 103.0], index=pd.to_datetime(["2020-01-02", "2020-01-03", "2020-01-06", "2020-01-07"]))
    out = fred_sp500_check(sp, f).iloc[0]
    assert out["n_common"] == 3                         # ngày "." của FRED bị bỏ
    assert abs(out["max_abs_diff_pct"] - 0.05) < 1e-9   # 102,051 / 102 − 1 = 0,05%
