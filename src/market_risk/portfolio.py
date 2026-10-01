"""Phase 1.5 — Lợi suất tài sản và danh mục (CLAUDE.md §4).

* Log return tài sản: r_t = ln(P_t / P_{t−1})
* S&P quy đổi VND:   r_SP_VND = r_SP_USD + r_USDVND
  (vì P^VND = P^USD × S ⇒ ln(P^VND_t/P^VND_{t−1}) = ln(P^USD_t/P^USD_{t−1}) + ln(S_t/S_{t−1}))
* Danh mục tái cân bằng hằng ngày: R_p = Σ w_i (e^{r_i} − 1), r_p = ln(1 + R_p)
  (cộng có trọng số **simple return** mới đúng; cộng log return như code cũ chỉ là xấp xỉ)
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import load_config, path_of


def asset_returns(prices: pd.DataFrame) -> pd.DataFrame:
    """Log return của VN, SP_USD, USDVND và SP_VND từ bảng giá đã ghép."""
    r = np.log(prices[["VN", "SP_USD", "USDVND"]]).diff().dropna()
    r["SP_VND"] = r["SP_USD"] + r["USDVND"]
    r.index.name = "Date"
    return r


def portfolio_return(r_a: pd.Series, r_b: pd.Series, w_a: float, w_b: float) -> pd.Series:
    """Log return danh mục 2 tài sản tái cân bằng hằng ngày: ln(1 + w_a(e^{r_a}−1) + w_b(e^{r_b}−1))."""
    simple = w_a * np.expm1(r_a) + w_b * np.expm1(r_b)
    return np.log1p(simple)


def build_portfolios(r: pd.DataFrame, weights: dict[str, list[float]], sp_col: str = "SP_VND") -> pd.DataFrame:
    """Tạo các danh mục VN–S&P theo dict ``{tên: [w_VN, w_SP]}``."""
    return pd.DataFrame({name: portfolio_return(r["VN"], r[sp_col], w[0], w[1])
                         for name, w in weights.items()}, index=r.index)


def run(prices: pd.DataFrame | None = None, cfg: dict | None = None) -> pd.DataFrame:
    """Ghi ``returns.parquet`` gồm tài sản + 3 danh mục chính + lưới + bản USD (không quy đổi)."""
    cfg = cfg or load_config()
    proc = path_of("processed", cfg)
    if prices is None:
        prices = pd.read_parquet(proc / "daily_prices.parquet")
    r = asset_returns(prices)
    main = build_portfolios(r, cfg["portfolios"]["main"])
    grid = build_portfolios(r, cfg["portfolios"]["grid"])
    usd = build_portfolios(r, {"VN50_SP50_USD": [0.5, 0.5]}, sp_col="SP_USD")
    out = pd.concat([r, main, grid[[c for c in grid if c not in ("W100_0", "W50_50", "W0_100")]], usd], axis=1)
    out.to_parquet(proc / "returns.parquet")
    lag = pd.read_parquet(proc / "daily_prices_lagged.parquet")
    rl = asset_returns(lag)
    pd.concat([rl, build_portfolios(rl, cfg["portfolios"]["main"])], axis=1).to_parquet(proc / "returns_lagged.parquet")
    return out


def load_returns(cfg: dict | None = None, lagged: bool = False) -> pd.DataFrame:
    """Đọc lại bảng lợi suất đã tính."""
    name = "returns_lagged.parquet" if lagged else "returns.parquet"
    return pd.read_parquet(path_of("processed", cfg) / name)


GRID_ALIAS = {"W100_0": "VN100", "W50_50": "VN50_SP50", "W0_100": "SP100"}
