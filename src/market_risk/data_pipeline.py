"""Nạp hai file clean của nhóm, kiểm tra chuỗi giá và tạo bảng dữ liệu dùng trong phân tích."""

from __future__ import annotations

import logging

import numpy as np
import pandas as pd

from .config import ROOT, load_config, path_of, save_table

log = logging.getLogger(__name__)


def validate(s: pd.Series, today: pd.Timestamp | None = None) -> None:
    """Kiểm tra thứ tự ngày, ngày trùng, giá dương và ngày tương lai."""
    today = today or pd.Timestamp.today().normalize()
    if not s.index.is_monotonic_increasing:
        raise ValueError(f"{s.name}: ngày không tăng dần")
    if s.index.duplicated().any():
        raise ValueError(f"{s.name}: có ngày trùng")
    if s.empty or s.isna().any() or not np.isfinite(s).all() or not (s > 0).all():
        raise ValueError(f"{s.name}: có giá không dương, thiếu hoặc không hữu hạn")
    if s.index.max() > today:
        raise ValueError(f"{s.name}: có ngày tương lai")


def top_moves(s: pd.Series, n: int = 10, alert: float | None = None) -> pd.DataFrame:
    """Xuất các biến động log return ngày lớn nhất kèm cờ cảnh báo."""
    returns = np.log(s).diff().dropna()
    top = returns.reindex(returns.abs().sort_values(ascending=False).index[:n])
    result = pd.DataFrame({"series": s.name, "Date": top.index, "log_return": top.values})
    result["rank"] = range(1, len(result) + 1)
    result["alert"] = result["log_return"].abs() > alert if alert else False
    if alert and result["alert"].any():
        log.warning("%s: %d ngày vượt ngưỡng cảnh báo %.0f%%", s.name, int(result["alert"].sum()), alert * 100)
    return result


def clean_fx_spikes(s: pd.Series, window: int = 15, threshold: float = 0.015,
                    n_iter: int = 1) -> tuple[pd.Series, pd.DataFrame]:
    """Lọc điểm lỗi nhập liệu của tỷ giá bằng bộ lọc Hampel, trả về (chuỗi sạch, nhật ký điểm bị lọc).

    Điểm lỗi: |ln(S_t / trung vị trượt ``window`` phiên căn giữa)| > ``threshold``. Tỷ giá VND được quản lý
    trong biên độ hẹp nên một mức giá lệch > 1,5% rồi quay về ngay là lỗi báo giá (vd. 01/12/2009: 18.275 →
    19.150 → 18.276). Đợt điều chỉnh tỷ giá thật (26/11/2009, 11/02/2010, 11/02/2011 +6,1%) giữ mức mới nên trung vị
    đi theo và không bị lọc; vì vậy chỉ lọc 1 vòng (vòng thứ hai bắt nhầm mức mới 27/11/2009).
    Bộ lọc chỉ dùng giá hai phía để **nhận diện** lỗi; điểm lỗi được thay bằng giá hợp lệ liền trước.
    """
    clean = s.copy()
    logs = []
    for it in range(n_iter):
        med = clean.rolling(window, center=True, min_periods=3).median()
        flag = np.log(clean / med).abs() > threshold
        if flag.any():
            logs.append(pd.DataFrame({"series": s.name, "Date": clean.index[flag].date, "value": clean[flag].values,
                                      "rule": f"Hampel lần {it + 1}: lệch >{threshold:.1%} so với trung vị {window} phiên",
                                      "action": "thay bằng giá hợp lệ trước đó"}))
        clean = clean.mask(flag)
    logdf = (pd.concat(logs, ignore_index=True) if logs
             else pd.DataFrame(columns=["series", "Date", "value", "rule", "action"]))
    return clean.ffill(), logdf


def fred_sp500_check(sp: pd.Series, path) -> pd.DataFrame:
    """T0b: đối chiếu giá S&P 500 trong file clean với chuỗi FRED ``SP500`` (nguồn đề án chỉ định).

    Chỉ để kiểm chứng — mô hình không đọc file FRED. FRED chỉ lưu S&P 500 10 năm gần nhất (từ 30/09/2016), nên đối
    chiếu trên các phiên trùng. Sai lệch tương đối |P_clean / P_FRED − 1|; tương quan tính trên log return.
    """
    fred = pd.read_csv(path, parse_dates=["observation_date"]).set_index("observation_date")["SP500"]
    fred = pd.to_numeric(fred, errors="coerce").dropna()          # FRED ghi "." cho ngày nghỉ
    j = pd.concat([sp.rename("clean"), fred.rename("fred")], axis=1, join="inner").dropna()
    diff = (j["clean"] / j["fred"] - 1).abs()
    r = np.log(j).diff().dropna()
    return pd.DataFrame([{
        "series": "S&P 500", "fred_series": "SP500", "n_common": len(j),
        "start": j.index.min().date(), "end": j.index.max().date(),
        "max_abs_diff_pct": 100 * diff.max(), "mean_abs_diff_pct": 100 * diff.mean(),
        "pct_days_diff_below_0_01pct": 100 * (diff < 1e-4).mean(),
        "corr_log_returns": r["clean"].corr(r["fred"]),
    }])


def merge_lagged(vn: pd.Series, sp: pd.Series, fx: pd.Series) -> pd.DataFrame:
    """Ghép phiên S&P gần nhất trước mỗi phiên VN để xử lý lệch giờ giao dịch."""
    left = vn.rename("VN").rename_axis("Date").reset_index()
    right = sp.rename("SP_USD").rename_axis("Date").reset_index()
    out = pd.merge_asof(left, right, on="Date", direction="backward", allow_exact_matches=False)
    return out.set_index("Date").join(fx.rename("USDVND").rename_axis("Date"), how="inner").dropna()


def _read_clean_prices(cfg: dict) -> pd.DataFrame:
    folder = ROOT / cfg["cleaned_files"]["directory"]
    path = folder / cfg["cleaned_files"]["daily"]
    if not path.is_file():
        raise FileNotFoundError(f"Không tìm thấy file dữ liệu clean: {path}")

    log.info("Đang đọc dữ liệu clean từ %s...", path)
    df = pd.read_csv(path)
    if df.empty:
        raise ValueError(f"{path}: file không có dữ liệu")
    required = {"Date", "Price_VNINDEX", "Price_SP500", "Price_USDVND"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"{path}: thiếu cột bắt buộc {', '.join(sorted(missing))}")

    dates = pd.to_datetime(df["Date"], format="%m/%d/%Y", errors="coerce")
    if dates.isna().any():
        dates = pd.to_datetime(df["Date"], format="ISO8601", errors="coerce")
    if dates.isna().any():
        bad_rows = dates.index[dates.isna()].tolist()[:5]
        raise ValueError(f"{path}: ngày không hợp lệ tại các dòng {bad_rows}")

    df["Date"] = dates
    df = df.set_index("Date")
    df.index.name = "Date"
    prices = pd.DataFrame({
        "VN": pd.to_numeric(df["Price_VNINDEX"], errors="raise").astype(float),
        "SP_USD": pd.to_numeric(df["Price_SP500"], errors="raise").astype(float),
        "USDVND": pd.to_numeric(df["Price_USDVND"], errors="raise").astype(float),
    }, index=df.index)
    for column in prices:
        validate(prices[column])
    return prices


def run(cfg: dict | None = None) -> pd.DataFrame:
    """Nạp duy nhất dữ liệu clean trong data/clean và ghi dữ liệu trung gian."""
    cfg = cfg or load_config()
    prices = _read_clean_prices(cfg)
    fc = cfg["fx_cleaning"]
    prices["USDVND"], fx_log = clean_fx_spikes(prices["USDVND"], fc["hampel_window"], fc["hampel_threshold"])
    save_table(fx_log, "T0_fx_cleaning_log")
    log.info("USDVND: lọc %d điểm lỗi báo giá (chi tiết T0_fx_cleaning_log)", len(fx_log))
    fred_path = ROOT / cfg["fred_check"]["sp500"]
    if fred_path.is_file():
        chk = fred_sp500_check(prices["SP_USD"], fred_path)
        save_table(chk, "T0b_fred_sp500_check")
        log.info("S&P 500 so với FRED SP500: %d phiên trùng, lệch tối đa %.4f%%",
                 int(chk["n_common"].iloc[0]), chk["max_abs_diff_pct"].iloc[0])
    else:
        log.warning("Không có %s — bỏ qua đối chiếu FRED", fred_path)
    lagged = merge_lagged(prices["VN"], prices["SP_USD"], prices["USDVND"])

    processed = path_of("processed", cfg)
    prices.to_parquet(processed / "daily_prices.parquet")
    lagged.to_parquet(processed / "daily_prices_lagged.parquet")

    rows = []
    for name in prices:
        series = prices[name]
        rows.append({
            "series": name,
            "N_raw": len(series),
            "N_clean": len(series),
            "n_flagged_errors": len(fx_log) if name == "USDVND" else 0,
            "start": series.index.min().date(),
            "end": series.index.max().date(),
            "n_missing": int(series.isna().sum()),
            "n_dup_dates": 0,
            "dropped_by_merge": 0,
            "pct_dropped_by_merge": 0.0,
        })
    rows.append({
        "series": "MERGED (inner)",
        "N_raw": len(prices),
        "N_clean": len(prices),
        "start": prices.index.min().date(),
        "end": prices.index.max().date(),
    })
    save_table(pd.DataFrame(rows), "T0_data_quality")

    alerts = cfg["jump_alert"]
    moves = pd.concat([
        top_moves(prices["VN"], 10, alerts["vn"]),
        top_moves(prices["SP_USD"], 10, alerts["sp"]),
        top_moves(prices["USDVND"], 10, alerts["fx"]),
    ], ignore_index=True)
    save_table(moves, "T0_top_moves")
    log.info("Đã dùng hai file clean: %d ngày giá; %d ngày ghép lệch pha", len(prices), len(lagged))
    return prices
