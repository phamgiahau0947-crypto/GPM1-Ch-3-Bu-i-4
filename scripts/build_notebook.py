"""Sinh notebooks/00_full_analysis.ipynb (mạch MT1 → MT5 → Application) bằng nbformat.

    python scripts/build_notebook.py
    jupyter nbconvert --to notebook --execute notebooks/00_full_analysis.ipynb --inplace
"""

import sys
from pathlib import Path

import nbformat as nbf

ROOT = Path(__file__).resolve().parents[1]
md, code = nbf.v4.new_markdown_cell, nbf.v4.new_code_cell

cells = [
    md("# Đề án 03 — Đo lường rủi ro thị trường: VaR, ES và kiểm định ngược\n"
       "**Danh mục Việt–Mỹ (VN-Index & S&P 500 quy đổi VND), theo khoảng thời gian trong hai file clean**\n\n"
       "> Câu hỏi trung tâm: *Phân bổ một phần danh mục từ VN-Index sang S&P 500 có giúp nhà đầu tư Việt Nam giảm "
       "rủi ro tổn thất lớn không, và lợi ích đó thay đổi thế nào trong các giai đoạn căng thẳng?*\n\n"
       "Notebook này **gọi hàm trong `src/market_risk`**; mọi tham số ở `config.yaml`, seed = 2026. "
       "Bước rolling dùng cache (`data/processed/rolling_cache`) nên chạy lại nhanh."),
    code("import sys, warnings\nfrom pathlib import Path\nROOT = Path.cwd().parent if Path.cwd().name == 'notebooks' else Path.cwd()\n"
         "sys.path.insert(0, str(ROOT / 'src'))\nwarnings.filterwarnings('ignore')\n"
         "import pandas as pd\nfrom IPython.display import Image, Markdown, display\n"
         "from market_risk.config import load_config, read_table, setup_logging\n"
         "from market_risk import data_pipeline, inflation, portfolio, descriptive, rolling, overall, diversification, "
         "fx_inflation, spillover, stress, application, plots, reporting\nfrom market_risk.backtest import runner as backtest\n"
         "cfg = load_config(); log = setup_logging('notebook')\npd.set_option('display.max_columns', 30); pd.set_option('display.width', 200)\n"
         "FIG = ROOT / 'outputs' / 'figures'\ndef fig(name): display(Image(filename=str(FIG / f'{name}.png'), width=900))"),
    md("## 1. Dữ liệu (Phase 1)\nHai file trong `data/clean/`: giá đóng cửa ngày VN-Index (HOSE), S&P 500 và tỷ giá USD/VND từ Investing.com; "
       "CPI Việt Nam theo tháng từ IMF IFS (2010 = 100), chỉ dùng để phân loại bối cảnh lạm phát. Giá S&P 500 được đối chiếu với FRED SP500 (T0b)."),
    code("prices = data_pipeline.run(cfg)\nmonthly = inflation.run(prices.index, cfg)\nret = portfolio.run(prices, cfg)\n"
         "display(read_table('T0_data_quality'))"),
    code("# Xem trước giá chuẩn hóa và lạm phát (các hình còn lại vẽ ở cuối)\nplots.f1_prices(prices, cfg); plots.f6_inflation(cfg)\n"
         "fig('F1_normalized_prices'); fig('F6_inflation_regime')"),
    md("## 2. Thống kê mô tả và kiểm định giả định (Phase 2)\nJarque–Bera/Anderson–Darling (chuẩn — giả định của Normal, MC_Normal), "
       "ADF/KPSS (tính dừng), ARCH-LM và Ljung–Box trên r² (biến động theo cụm — căn cứ dùng GARCH)."),
    code("print(descriptive.run(cfg=cfg))\ndisplay(read_table('T1_descriptive').query(\"period=='Toàn kỳ'\"))\n"
         "read_table('T2_assumption_tests')[['label','test','statistic','p_value','conclusion']]"),
    md("## 3. MT1 — Ước lượng VaR/ES bằng bốn phương pháp, rolling 252 phiên (Phase 3–4)\n"
       "Mô phỏng lịch sử (HS), phương pháp tham số chuẩn (Normal), Monte Carlo chuẩn (MC_Normal) "
       "và GARCH(1,1)-Normal (GARCH_N)."),
    code("fc = rolling.run(cfg)\nprint(overall.run(cfg))\nt4 = read_table('T4_var_es_overall')\n"
         "t4[t4['sample']=='common'].pivot(index='model', columns='portfolio', values='ES_975').mul(100).round(2)"),
    code("display(read_table('T3_garch_params')[['series','model','mu','omega','alpha','beta','persistence','half_life_days','BIC']])"),
    md("## 4. MT4 — Kiểm định ngược VaR (Phase 5)\nChỉ sử dụng Kupiec (tần suất vi phạm) và Christoffersen (độc lập, bao phủ có điều kiện). ES được báo cáo như thước đo rủi ro, không có kiểm định ES."),
    code("bt = backtest.run(cfg=cfg)\nt5 = bt['T5']\n"
         "t5[(t5.set=='main')&(t5.level==0.99)][['portfolio','model','T','x','expected','rate','p_uc','p_ind','p_cc','conclusion']]"),
    md("## 5. MT2 — Lợi ích đa dạng hóa theo thời gian (Phase 6)\n*Phân tích mô tả — 'đi kèm với', không phải 'gây ra'.*"),
    code("print(diversification.run(cfg))\nread_table('T8_diversification_by_corr').query(\"corr_measure=='corr_252'\")"),
    md("## 6. MT3 — Tỷ giá và bối cảnh lạm phát (Phase 7) + VAR/Granger (Bài 9)"),
    code("print(fx_inflation.run(cfg))\nprint(spillover.run(cfg))\n"
         "display(read_table('T9_fx_effect').query(\"period=='Toàn kỳ'\"))\ndisplay(read_table('T10_inflation_regimes').query(\"split=='ngưỡng 4%'\"))"),
    md("## 7. MT5 — Stress test 2008, 2018, 2020, 2022 (Phase 8)"),
    code("print(stress.run(cfg))\ndisplay(read_table('T11b_stress_worst_models')[['period','portfolio','role','model','UR_VaR99','UR_ES']])\n"
         "display(read_table('T12_stress_hypothetical'))"),
    md("## 8. Application — phân bổ theo giới hạn ES và khuyến nghị mô hình (Phase 9)"),
    code("text = application.run(cfg)\ndisplay(Markdown(text))\nread_table('T15_model_recommendation')"),
    md("## 9. Hình (Phase 10)"),
    code("plots.run(cfg); reporting.run(cfg)\n"
         "for f in ['F7_var_paths_VN50_SP50','F8_crisis_zoom','F9_exceedances','F10_rolling_corr','F11_div_benefit',"
         "'F12_es_by_weight_GARCH_N','F14_backtest_heatmap','F16_inflation_regime_es','F17_component_es','F18_var_irf']:\n    fig(f)"),
    md("## 9b. Kiểm tra tái lập\nSo các chỉ tiêu then chốt với bộ tham chiếu của nhóm (`outputs/reproducibility/tham_chieu.json`)."),
    code("import subprocess\nr = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'verify_reproducibility.py')], capture_output=True, "
         "text=True, encoding='utf-8', cwd=ROOT)\nprint(r.stdout[-700:])"),
    md("## 10. Hạn chế\n- Tỷ giá lấy từ file giá clean, đã lọc 3 điểm lỗi báo giá (T0_fx_cleaning_log); T9c so sánh toàn mẫu với mẫu con từ 2014.\n"
       "- Lệch múi giờ VN–Mỹ: phiên Mỹ đóng cửa sau phiên VN; robustness với dữ liệu lệch pha.\n"
       "- Lạm phát chỉ để chia bối cảnh, không kết luận nhân quả; chuỗi CPI lấy từ file clean thứ hai.\n"
       "- Chỉ số không phải tài sản đầu tư trực tiếp; bỏ qua phí, thuế, hạn chế chuyển vốn."),
]
nb = nbf.v4.new_notebook(cells=cells, metadata={"kernelspec": {"name": "python3", "display_name": "Python 3", "language": "python"},
                                                "language_info": {"name": "python"}})
out = ROOT / "notebooks" / "00_full_analysis.ipynb"
nbf.write(nb, out)
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
print(f"Đã ghi {out}")
