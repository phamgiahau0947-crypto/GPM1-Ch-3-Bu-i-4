"""Phase 1.4–1.5: lạm phát từ CPI, lợi suất danh mục."""
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from market_risk.config import load_config
from market_risk.inflation import classify_regimes, load_cpi_cleaned, map_to_daily
from market_risk.portfolio import asset_returns, build_portfolios


def test_cpi_imf_file_base_2010_and_known_inflation():
    m = load_cpi_cleaned()
    assert abs(m.loc["2010", "CPI_index"].mean() - 100) < 0.5                 # IMF IFS: chỉ số gốc 2010 = 100
    assert abs(m.loc["2008-12-01", "inflation_yoy"] - 0.1989) < 5e-4          # lạm phát 12/2008 công bố 19,89%
    assert m["inflation_yoy"].notna().all()


def test_cpi_inconsistent_inflation_column_is_rejected(tmp_path):
    cfg = load_config()
    src = Path(cfg["cleaned_files"]["directory"]) / cfg["cleaned_files"]["cpi"]
    d = pd.read_csv(Path(__file__).resolve().parents[1] / src)
    d.loc[30, "Inflation_YoY"] += 1.0                                         # sửa tay 1 điểm % → phải bị phát hiện
    d.to_csv(tmp_path / "cpi.csv", index=False)
    cfg["cleaned_files"] = {**cfg["cleaned_files"], "directory": str(tmp_path), "cpi": "cpi.csv"}
    with pytest.raises(ValueError, match="Inflation_YoY lệch"):
        load_cpi_cleaned(cfg)


def test_regimes_and_publication_lag():
    infl = pd.Series([0.02, 0.05, 0.03], index=pd.date_range("2020-01-01", periods=3, freq="MS"))
    reg = classify_regimes(infl, 0.04)
    assert list(reg["regime"]) == ["Thấp", "Cao", "Thấp"]
    days = pd.to_datetime(["2020-02-10", "2020-03-10"])
    same = map_to_daily(reg[["regime"]], days, 0)["regime"].tolist()
    pub = map_to_daily(reg[["regime"]], days, 1)["regime"].tolist()
    assert same == ["Cao", "Thấp"] and pub == ["Thấp", "Cao"]


def test_portfolio_returns():
    rng = np.random.default_rng(0)
    p = pd.DataFrame(np.exp(np.cumsum(rng.normal(0, 0.01, (50, 3)), 0)) * [1000, 3000, 23000],
                     columns=["VN", "SP_USD", "USDVND"], index=pd.bdate_range("2020-01-01", periods=50))
    r = asset_returns(p)
    direct = np.log(p["SP_USD"] * p["USDVND"]).diff().dropna()
    assert np.max(np.abs(r["SP_VND"] - direct)) < 1e-12
    ports = build_portfolios(r, {"VN100": [1, 0], "SP100": [0, 1], "H": [0.5, 0.5]})
    assert np.max(np.abs(ports["VN100"] - r["VN"])) < 1e-12
    assert np.max(np.abs(ports["SP100"] - r["SP_VND"])) < 1e-12
    expected = np.log(0.5 * np.exp(r["VN"]) + 0.5 * np.exp(r["SP_VND"]))
    assert np.max(np.abs(ports["H"] - expected)) < 1e-12
