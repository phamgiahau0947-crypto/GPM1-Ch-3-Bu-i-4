"""Phase 5: kiểm định ngược với giá trị biết trước."""
import numpy as np

from market_risk.backtest.var_tests import christoffersen, kupiec


def test_kupiec_size_monte_carlo():
    rng = np.random.default_rng(2026)
    hits = rng.random((10_000, 1000)) < 0.01
    rej = np.mean([kupiec(h, 0.01)["p_uc"] < 0.05 for h in hits])
    assert 0.03 <= rej <= 0.07


def test_kupiec_hand_example():
    # Tính tay: T = 250, x = 5, p = 1%:
    # LR = −2[245 ln 0,99 + 5 ln 0,01] + 2[245 ln 0,98 + 5 ln 0,02] ≈ 1,956
    assert abs(kupiec(np.r_[np.ones(5), np.zeros(245)], 0.01)["LR_uc"] - 1.956) < 1e-3


def test_kupiec_jorion_nonrejection_regions():
    # Jorion (2006), bảng vùng không bác bỏ ở mức 95% cho p = 1% (theo Kupiec 1995):
    # T = 252: N < 7;  T = 1000: 4 < N < 17
    def p(T, x):
        return kupiec(np.r_[np.ones(x), np.zeros(T - x)], 0.01)["p_uc"]
    assert p(252, 6) > 0.05 and p(252, 7) < 0.05
    assert p(1000, 5) > 0.05 and p(1000, 16) > 0.05
    assert p(1000, 4) < 0.05 and p(1000, 17) < 0.05


def test_kupiec_edge_cases():
    assert np.isfinite(kupiec(np.zeros(500), 0.01)["LR_uc"])
    assert np.isfinite(kupiec(np.ones(20), 0.01)["LR_uc"])


def test_christoffersen_detects_clustering():
    h = np.zeros(1000, dtype=int)
    for s in (100, 400, 700):
        h[s:s + 4] = 1                                 # 12 vi phạm dồn thành 3 cụm
    res = christoffersen(h, 0.01)
    assert res["p_uc"] > 0.05 and res["p_ind"] < 0.01


def test_christoffersen_n11_zero():
    h = np.zeros(500, dtype=int)
    h[[50, 150, 300]] = 1
    res = christoffersen(h, 0.01)
    assert res["n11"] == 0 and np.isfinite(res["LR_ind"])


def test_christoffersen_requires_at_least_two_observations():
    for hits in (np.array([], dtype=int), np.array([0])):
        result = christoffersen(hits, 0.01)
        assert result["T"] == hits.size
        assert np.isnan(result["LR_ind"]) and np.isnan(result["p_cc"])
    assert np.isnan(kupiec(np.array([], dtype=int), 0.01)["p_uc"])
