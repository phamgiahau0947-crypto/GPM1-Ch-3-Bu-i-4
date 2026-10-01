# Đề án 03 — Đo lường rủi ro thị trường: VaR, ES và kiểm định ngược

Đây là **hướng dẫn chạy duy nhất** dành cho thành viên nhóm và người chấm.

## Chạy trên Windows

1. Giải nén dự án vào đường dẫn ngắn, ví dụ `C:\DeAn03`. Cần Python 3.11, 3.12 hoặc 3.13 và Internet cho lần cài đặt đầu tiên.
2. Nhấp đúp **`CHAY_DU_AN.bat`**. Lần đầu, file tự tạo môi trường `.venv`, cài thư viện rồi mở dashboard. Những lần sau, file bỏ qua cài đặt và mở dashboard ngay.
3. Trong dashboard, chọn **Vận hành → Chạy phân tích** rồi bấm **Bắt đầu chạy toàn bộ** (khoảng 6 phút). Giữ cửa sổ terminal mở trong lúc chạy; có thể xem trang khác, quay lại trang này để theo dõi tiến trình.
4. Chọn **Vận hành → Kiểm tra tái lập** rồi bấm **Kiểm tra ngay**: máy so các con số then chốt với bộ tham chiếu của nhóm và mã MD5 của hai file dữ liệu → **KHỚP / GẦN KHỚP / LỆCH**.

Chạy toàn bộ gồm nạp và kiểm tra dữ liệu, thống kê mô tả và kiểm định giả định, bốn phương pháp VaR/ES theo đề — HS, Normal, MC_Normal và GARCH_N (GARCH(1,1)-Normal) — dự báo cuốn chiếu, backtest VaR bằng Kupiec và Christoffersen, ES 97,5%, stress test 2008, Việt Nam 2011–2012, 2018, 2020 và 2022, bảng, hình và báo cáo. Dashboard cũng có **Chạy lại nhanh** (tái sử dụng cache) và **Chạy kiểm thử**.

> Bản nộp đã có sẵn kết quả của lần chạy đầy đủ gần nhất, nên mở dashboard là xem được ngay. Bấm **Bắt đầu chạy toàn bộ** để tự tính lại từ dữ liệu.

## Dữ liệu đầu vào và kết quả

Mô hình chỉ dùng đúng hai file:

- `data\clean\cleaned_daily_data.csv` — giá đóng cửa ngày VN-Index (HOSE), S&P 500 và tỷ giá giao dịch USD/VND, trích xuất từ Investing.com.
- `data\clean\cleaned_cpi_inflation.csv` — CPI Việt Nam từ IMF International Financial Statistics (IFS), tần suất tháng, chỉ số gốc 2010 = 100; lạm phát so cùng kỳ π = CPI_t / CPI_(t−12) − 1 (code kiểm tra cột lạm phát khớp công thức này khi nạp).

Không tải dữ liệu từ Internet khi chạy. File `data\fred\SP500.csv` (chuỗi FRED `SP500` — nguồn đề án chỉ định, tải sẵn) chỉ dùng để đối chiếu giá S&P 500, mô hình không đọc file này. Tỷ giá có 3 điểm lỗi báo giá (12/2009, giá lệch rồi quay về ngay) được lọc tự động và ghi lại ở `outputs\tables\T0_fx_cleaning_log.csv`. Giá S&P 500 trong file khớp chuỗi FRED tới 0,0024% trên 2.036 phiên từ 30/09/2016 (`outputs\tables\T0b_fred_sp500_check.csv`). Dữ liệu trung gian trong `data\processed\` được tạo lại khi chạy.

## Cấu trúc thư mục

```
CHAY_DU_AN.bat          nhấp đúp: cài môi trường (lần đầu) và mở dashboard
config.yaml             mọi tham số (seed 2026, cửa sổ, mức tin cậy, giai đoạn stress…)
data/clean/             hai file dữ liệu đầu vào
data/fred/SP500.csv     chuỗi FRED SP500 (chỉ để đối chiếu giá S&P 500, bảng T0b)
src/market_risk/        mã nguồn: dữ liệu, 4 mô hình (models/), rolling, backtest/, đa dạng hóa, tỷ giá & lạm phát,
                        VAR, stress test, khuyến nghị, hình, xuất bảng
scripts/                run_all.py (chạy toàn bộ), verify_reproducibility.py (kiểm tra tái lập), build_notebook.py
dashboard/              giao diện Streamlit
notebooks/              00_full_analysis.ipynb — toàn bộ phân tích trong một notebook
tests/                  unit test (công thức có giá trị biết trước, chống look-ahead, dữ liệu mẫu)
outputs/tables/         các bảng kết quả T0, T0b, T1–T5, T5b, T8–T16 và các bảng phụ (CSV; bảng chính có thêm Markdown, LaTeX), cùng MT_answers.md
outputs/figures/        các hình F1–F14, F16–F19 (PNG + PDF 300 dpi); F7 và F12 có phiên bản theo danh mục/mô hình
outputs/reproducibility/tham_chieu.json   bộ số tham chiếu cho kiểm tra tái lập
docs/                   báo cáo, phương pháp luận, cẩm nang vấn đáp, tổng quan tài liệu, nhật ký sử dụng AI
```

| Bảng | Nội dung | Mục tiêu |
|---|---|---|
| T0, T0b, T1, T2 | chất lượng dữ liệu, lọc tỷ giá, đối chiếu FRED; thống kê mô tả; kiểm định giả định (chuẩn, dừng, ARCH) | nền |
| T3, T4 | tham số GARCH(1,1); VaR/ES 97,5% theo mô hình × danh mục | MT1 |
| T5, T5b, T13 | Kupiec, Christoffersen; bảng đạt/không đạt; robustness cửa sổ, refit, lệch pha | MT4 |
| T8 | lợi ích đa dạng hóa theo tương quan, Newey–West, tương quan đuôi, DCC, Forbes–Rigobon | MT2 |
| T9, T10, T16 | vai trò tỷ giá (ΔES, component ES), chế độ lạm phát, mô hình VAR | MT3 |
| T11, T12 | stress test lịch sử và kịch bản giả định | MT5 |
| T14, T15 | ES theo lưới tỷ trọng, xếp hạng và khuyến nghị mô hình | Khuyến nghị |

## Xử lý sự cố

- Nếu chưa cài Python, cài Python 3.12 (Windows installer 64-bit), đánh dấu **Add python.exe to PATH**, sau đó mở lại `CHAY_DU_AN.bat`.
- Nếu trình duyệt không tự mở, truy cập `http://localhost:8501`.
- Nếu dashboard đã chạy, launcher sẽ mở lại trang đó thay vì tạo tiến trình thứ hai. Nếu cổng 8501 bị ứng dụng khác chiếm, đóng ứng dụng đó rồi chạy lại.
- Nếu cài thư viện lỗi, kiểm tra kết nối Internet và phiên bản Python 3.11–3.13. Nhật ký phân tích nằm trong thư mục `outputs\logs\` (ví dụ `run_all_all.log`).
- Không xóa `.venv` hoặc `outputs` để xử lý lỗi nếu chưa cần; hỏi người quản lý dự án trước khi xóa dữ liệu kết quả.

## Dành cho người phát triển

Mở PowerShell tại thư mục dự án, kích hoạt môi trường đã được launcher tạo, rồi chạy:

```powershell
.\.venv\Scripts\Activate.ps1
python scripts\run_all.py all --fresh
python scripts\verify_reproducibility.py
python -m pytest -q
python -m pip install -r requirements-dev.txt
python -m ruff check .
```

Notebook phân tích dùng `nbformat`, `nbconvert` và `ipykernel`; có thể mở/chạy trong VS Code hoặc thực thi bằng `jupyter nbconvert`. Không cần cài giao diện JupyterLab riêng.

Tham số mô hình và seed 2026 nằm trong `config.yaml`. Chi tiết thiết kế nghiên cứu, công thức và quyết định của nhóm nằm trong `CLAUDE.md` và `docs\methodology.md`.
