"""Kiểm tra tái lập: so kết quả vừa chạy với bộ số tham chiếu của nhóm.

    python scripts/verify_reproducibility.py                    # kiểm tra (sau khi đã chạy run_all.py all)
    python scripts/verify_reproducibility.py --update-reference # nhóm tạo lại bộ tham chiếu (KHÔNG dùng khi chấm)

Kiểm tra 3 nhóm:
1. Dữ liệu đầu vào: mã MD5 của các file thuộc nguồn đang chọn khớp bộ tham chiếu.
2. Môi trường: phiên bản Python và thư viện so với requirements.txt (chỉ cảnh báo).
3. Kết quả: các con số then chốt (số phiên, VaR/ES, số vi phạm, lợi ích đa dạng hóa, lạm phát, stress, thứ hạng mô hình).
   Bộ tham chiếu chỉ so sánh được khi nguồn dữ liệu trùng nhau. KHỚP nếu |a − b| ≤ 1e−8 + 1e−4·|b|;
   GẦN KHỚP nếu sai lệch tương đối ≤ 1% (khác biệt số học giữa máy/CPU
   trong tối ưu GARCH); LỆCH nếu lớn hơn.
Kết quả ghi ở outputs/reproducibility/: BAO_CAO_TAI_LAP.html, bao_cao_tai_lap.md, ket_qua_kiem_tra.json.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import html
import json
import platform
import sys
from importlib import metadata
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

ROOT = Path(__file__).resolve().parents[1]
TABLES = ROOT / "outputs" / "tables"
OUT = ROOT / "outputs" / "reproducibility"
REF = OUT / "tham_chieu.json"
RTOL, ATOL, NEAR = 1e-4, 1e-8, 1e-2


def md5(p: Path) -> str:
    return hashlib.md5(p.read_bytes()).hexdigest()


def data_manifest(cfg: dict) -> dict[str, str]:
    folder = ROOT / cfg["cleaned_files"]["directory"]
    files = (folder / cfg["cleaned_files"][key] for key in ("daily", "cpi"))
    missing = [path for path in files if not path.is_file()]
    if missing:
        raise FileNotFoundError("Thiếu file đầu vào clean: " + ", ".join(str(path) for path in missing))
    return {path.relative_to(ROOT).as_posix(): md5(path) for path in (
        folder / cfg["cleaned_files"]["daily"], folder / cfg["cleaned_files"]["cpi"],
    )}


def t(name: str) -> pd.DataFrame:
    return pd.read_csv(TABLES / f"{name}.csv", encoding="utf-8-sig")


def fingerprint() -> dict[str, float]:
    """Các con số then chốt dùng để so khớp (tên → giá trị)."""
    fp: dict[str, float] = {}
    q = t("T0_data_quality")
    fp["Dữ liệu | số phiên sau ghép"] = float(q.loc[q["series"] == "MERGED (inner)", "N_clean"].iloc[0])
    fp["Dữ liệu | số điểm lỗi tỷ giá đã lọc"] = float(q.loc[q["series"] == "USDVND", "n_flagged_errors"].iloc[0])
    if (TABLES / "T0b_fred_sp500_check.csv").exists():
        f = t("T0b_fred_sp500_check").iloc[0]
        fp["Dữ liệu | S&P 500 vs FRED: số phiên trùng"] = float(f["n_common"])
        fp["Dữ liệu | S&P 500 vs FRED: lệch tối đa %"] = float(f["max_abs_diff_pct"])
    t2 = t("T2_assumption_tests")
    for r in t2[t2["test"].isin(["Jarque–Bera", "ARCH-LM(10)"])].itertuples():
        fp[f"Giả định | {r.test} | {r.series}"] = r.statistic
    t4 = t("T4_var_es_overall")
    for r in t4[t4["sample"] == "common"].itertuples():
        fp[f"MT1 | ES97,5 TB | {r.portfolio} | {r.model}"] = r.ES_975
        fp[f"MT1 | VaR99 TB | {r.portfolio} | {r.model}"] = r.VaR_99
    t5 = t("T5_backtest_var")
    for r in t5[(t5["set"] == "main") & (t5["level"] == 0.99)].itertuples():
        fp[f"MT4 | số vi phạm VaR99 | {r.portfolio} | {r.model}"] = float(r.x)
    t8 = t("T8_diversification_by_corr")
    for r in t8[(t8["model"] == "GARCH_N") & (t8["metric"] == "DR") & (t8["corr_measure"] == "corr_252")].itertuples():
        fp[f"MT2 | DR theo tam phân vị tương quan | {r.tercile}"] = r.mean
    t10 = t("T10_inflation_regimes")
    for r in t10[t10["split"] == "ngưỡng 4%"].itertuples():
        fp[f"MT3 | {r.metric} | lạm phát cao"] = r.mean_Cao
        fp[f"MT3 | {r.metric} | lạm phát thấp"] = r.mean_Thap
    t11 = t("T11_stress_historical")
    core = t11[t11["period"].isin(["GFC_2008", "TradeWar_2018", "COVID_2020", "Tightening_2022"])]
    for m, v in core.groupby("model")["UR_VaR99"].mean().items():
        fp[f"MT5 | vi phạm/kỳ vọng TB | {m}"] = v
    t14 = t("T14_allocation_es_limits")
    for r in t14[t14["period"] == "Toàn kỳ"].itertuples():
        fp[f"Application | ES TB | {r.model} | {r.weight}"] = r.ES_mean
    for r in t("T15_model_recommendation").itertuples():
        fp[f"Khuyến nghị | hạng tổng | {r.model}"] = float(r.overall_rank)
    return {k: float(v) for k, v in fp.items() if pd.notna(v)}


def environment() -> list[dict]:
    rows = [{"mục": "Python", "yêu cầu": ">=3.11", "đang dùng": platform.python_version(),
             "ok": sys.version_info >= (3, 11)}]
    for line in (ROOT / "requirements.txt").read_text(encoding="utf-8").splitlines():
        line = line.split("#")[0].strip()
        if "==" not in line:
            continue
        name, ver = line.split("==")
        try:
            have = metadata.version(name)
        except metadata.PackageNotFoundError:
            have = "chưa cài"
        rows.append({"mục": name, "yêu cầu": ver, "đang dùng": have, "ok": have == ver})
    return rows


def compare(cur: dict, ref: dict) -> pd.DataFrame:
    rows = []
    for k, b in ref.items():
        a = cur.get(k, np.nan)
        diff = abs(a - b) if np.isfinite(a) else np.inf
        rel = diff / max(abs(b), 1e-12)
        status = "KHỚP" if diff <= ATOL + RTOL * abs(b) else ("GẦN KHỚP" if rel <= NEAR else "LỆCH")
        rows.append({"chỉ tiêu": k, "tham chiếu": b, "lần chạy này": a, "sai lệch tương đối": rel, "trạng thái": status})
    for k in set(cur) - set(ref):
        rows.append({"chỉ tiêu": k, "tham chiếu": np.nan, "lần chạy này": cur[k], "sai lệch tương đối": np.nan,
                     "trạng thái": "MỚI"})
    return pd.DataFrame(rows)


def write_reports(res: pd.DataFrame, data_rows: list[dict], env: list[dict], verdict: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    now = dt.datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    counts = res["trạng thái"].value_counts().to_dict()
    n_data_bad = sum(not r["ok"] for r in data_rows)
    summary = {"thời điểm": now, "kết luận": verdict, "số chỉ tiêu": len(res), "đếm": counts,
               "dữ liệu đầu vào không khớp": n_data_bad, "python": platform.python_version(),
               "môi trường khác yêu cầu": [r["mục"] for r in env if not r["ok"]]}
    (OUT / "ket_qua_kiem_tra.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    res.to_csv(OUT / "chi_tiet_so_khop.csv", index=False, encoding="utf-8-sig")
    md = [f"# Báo cáo kiểm tra tái lập — {now}", "", f"**KẾT LUẬN: {verdict}**", "",
          f"- Số chỉ tiêu so khớp: {len(res)} — " + ", ".join(f"{k}: {v}" for k, v in counts.items()),
          f"- File dữ liệu đầu vào không khớp tham chiếu: {n_data_bad}", f"- Python: {platform.python_version()}", ""]
    bad = res[res["trạng thái"].isin(["LỆCH", "GẦN KHỚP"])]
    if len(bad):
        md += ["## Chỉ tiêu chưa khớp tuyệt đối", "", bad.to_markdown(index=False), ""]
    (OUT / "bao_cao_tai_lap.md").write_text("\n".join(md), encoding="utf-8")
    color = {"KHỚP": "#1a7f37", "GẦN KHỚP": "#9a6700", "LỆCH": "#cf222e", "MỚI": "#57606a"}
    rows = "".join(
        f"<tr><td>{html.escape(r['chỉ tiêu'])}</td><td>{r['tham chiếu']:.6g}</td><td>{r['lần chạy này']:.6g}</td>"
        f"<td>{r['sai lệch tương đối']:.2e}</td><td style='color:{color.get(r['trạng thái'])};font-weight:600'>"
        f"{r['trạng thái']}</td></tr>" for _, r in res.iterrows())
    drows = "".join(f"<tr><td>{html.escape(r['file'])}</td><td>{'✅ khớp tham chiếu' if r['ok'] else '⚠️ không khớp / không thể so sánh'}</td></tr>"
                    for r in data_rows)
    erows = "".join(f"<tr><td>{r['mục']}</td><td>{r['yêu cầu']}</td><td>{r['đang dùng']}</td>"
                    f"<td>{'✅' if r['ok'] else '⚠️ khác (thường vẫn chạy được)'}</td></tr>" for r in env)
    banner = {"KHỚP": "#dafbe1", "GẦN KHỚP": "#fff8c5"}.get(verdict.split(" —")[0], "#ffebe9")
    page = f"""<!doctype html><html lang="vi"><head><meta charset="utf-8"><title>Kiểm tra tái lập — Đề án 03</title>
<style>body{{font-family:Segoe UI,Arial,sans-serif;max-width:1100px;margin:24px auto;padding:0 16px;color:#1f2328}}
table{{border-collapse:collapse;width:100%;font-size:13px}}td,th{{border:1px solid #d0d7de;padding:4px 8px;text-align:left}}
th{{background:#f6f8fa}}.b{{background:{banner};padding:16px;border-radius:8px;font-size:20px;font-weight:700}}</style></head>
<body><h1>Kiểm tra tái lập — Đề án 03 (VaR, ES &amp; Backtesting)</h1><p>Thời điểm: {now}</p>
<div class="b">KẾT LUẬN: {html.escape(verdict)}</div>
<p>Số chỉ tiêu: {len(res)} — {html.escape(', '.join(f'{k}: {v}' for k, v in counts.items()))}.
KHỚP: sai lệch ≤ 0,01%; GẦN KHỚP: ≤ 1% (khác biệt số học giữa các máy khi tối ưu GARCH); LỆCH: &gt; 1%.</p>
<h2>1. Dữ liệu đầu vào (MD5)</h2><table><tr><th>File</th><th>Đối chiếu</th></tr>{drows}</table>
<h2>2. Môi trường</h2><table><tr><th>Thành phần</th><th>Yêu cầu</th><th>Đang dùng</th><th></th></tr>{erows}</table>
<h2>3. So khớp kết quả</h2><table><tr><th>Chỉ tiêu</th><th>Tham chiếu</th><th>Lần chạy này</th><th>Sai lệch tương đối</th>
<th>Trạng thái</th></tr>{rows}</table></body></html>"""
    (OUT / "BAO_CAO_TAI_LAP.html").write_text(page, encoding="utf-8")


def main() -> int:
    for s in (sys.stdout, sys.stderr):
        try:
            s.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    ap = argparse.ArgumentParser()
    ap.add_argument("--update-reference", action="store_true", help="tạo lại bộ tham chiếu (chỉ nhóm dùng)")
    args = ap.parse_args()
    if not (TABLES / "T15_model_recommendation.csv").exists():
        print("CHƯA CÓ KẾT QUẢ: hãy chạy phân tích trước (CHAY_DU_AN.bat → dashboard, hoặc python scripts/run_all.py all).")
        return 2
    cfg = yaml.safe_load((ROOT / "config.yaml").read_text(encoding="utf-8"))
    source = "cleaned"
    manifest = data_manifest(cfg)
    if args.update_reference:
        OUT.mkdir(parents=True, exist_ok=True)
        REF.write_text(json.dumps({"tạo lúc": dt.datetime.now().isoformat(timespec="seconds"),
                                   "python": platform.python_version(), "nguồn dữ liệu": source,
                                   "mô hình": cfg["models_main"], "backtest": ["Kupiec", "Christoffersen"],
                                   "dữ liệu đầu vào": manifest, "chỉ tiêu": fingerprint()},
                                  ensure_ascii=False, indent=1), encoding="utf-8")
        print(f"Đã ghi bộ tham chiếu: {len(manifest)} file dữ liệu nguồn {source} → {REF}")
        return 0
    ref = json.loads(REF.read_text(encoding="utf-8"))
    ref_source = ref.get("nguồn dữ liệu", "raw")
    source_matches = source == ref_source
    models_match = cfg["models_main"] == ref.get("mô hình")
    backtests_match = ["Kupiec", "Christoffersen"] == ref.get("backtest")
    ref_manifest = ref.get("dữ liệu đầu vào", ref.get("dữ liệu gốc", {}))
    data_rows = [{"file": f, "ok": source_matches and ref_manifest.get(f) == h} for f, h in manifest.items()]
    res = compare(fingerprint(), ref["chỉ tiêu"]) if source_matches and models_match and backtests_match else pd.DataFrame(
        columns=["chỉ tiêu", "tham chiếu", "lần chạy này", "sai lệch tương đối", "trạng thái"])
    env = environment()
    n_bad = int((res["trạng thái"] == "LỆCH").sum())
    n_near = int((res["trạng thái"] == "GẦN KHỚP").sum())
    data_bad = sum(not r["ok"] for r in data_rows)
    if not models_match or not backtests_match:
        verdict = (
            "KHÔNG SO SÁNH — bộ tham chiếu chưa được tạo cho cấu hình mô hình và hai kiểm định hiện tại; "
            "cần cập nhật tham chiếu sau khi kiểm tra kết quả"
        )
    elif not source_matches:
        verdict = f"KHÔNG SO SÁNH — bộ tham chiếu dùng nguồn {ref_source}, lần chạy hiện tại dùng {source}"
    elif data_bad:
        verdict = f"LỆCH — {data_bad} file dữ liệu đầu vào không khớp tham chiếu"
    elif n_bad:
        verdict = f"LỆCH — {n_bad}/{len(res)} chỉ tiêu sai lệch > 1%"
    elif n_near:
        verdict = f"GẦN KHỚP — {len(res) - n_near}/{len(res)} chỉ tiêu khớp tuyệt đối, {n_near} chênh ≤ 1% (sai số số học)"
    else:
        verdict = f"KHỚP — cả {len(res)} chỉ tiêu trùng với kết quả của nhóm"
    write_reports(res, data_rows, env, verdict)
    print("=" * 70)
    print(f"KẾT LUẬN KIỂM TRA TÁI LẬP: {verdict}")
    print(f"Báo cáo chi tiết: {OUT / 'BAO_CAO_TAI_LAP.html'}")
    print("=" * 70)
    return 0 if source_matches and models_match and backtests_match and not (n_bad or data_bad) else 1


if __name__ == "__main__":
    sys.exit(main())
