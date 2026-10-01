"""Mô phỏng lịch sử (Historical Simulation / HS).

Tài liệu: Jorion (2006, ch. 10).
"""

from __future__ import annotations

from collections.abc import Sequence

import numpy as np

from ._common import DEFAULT_ES, DEFAULT_VAR, empirical_result


def forecast_hs(returns_window: np.ndarray, var_levels: Sequence[float] = DEFAULT_VAR,
                es_level: float = DEFAULT_ES, **kw) -> dict:
    """Historical Simulation.

    VaR_q = −Q̂_{1−q}(r_{t−W+1..t}) với Q̂ là phân vị mẫu **nội suy tuyến tính** (numpy
    ``method='linear'``, Hyndman–Fan loại 7).
    ES_q  = −trung bình các lợi suất ≤ Q̂_{1−q}  (lỗ vượt VaR 97,5%).

    Giả định: phân phối lợi suất tương lai giống phân phối thực nghiệm trong cửa sổ
    (i.i.d., không thay đổi theo thời gian). Không cần giả định dạng phân phối.
    """
    r = np.asarray(returns_window, dtype=float)
    return empirical_result(r, var_levels, es_level, {"n": len(r)})
