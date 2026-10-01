# CLAUDE.md — Bộ nhớ dự án (Claude Code đọc file này mỗi phiên)

## 1. Bối cảnh học phần

- Đề án nhóm **số 03**, môn "Gói phần mềm Ứng dụng trong Tài chính 1" (UEL, 2026–2027).
- Tên đề tài: **Đo lường rủi ro thị trường: VaR, ES và kiểm định ngược** (Market Risk Measurement & Backtesting).
- Yêu cầu gốc của giảng viên:
  1. Danh mục kết hợp VN-Index và S&P 500.
  2. VaR theo 3 phương pháp: lịch sử, tham số, Monte Carlo.
  3. GARCH(1,1); Expected Shortfall 97,5% theo FRTB.
  4. Kiểm định Kupiec và Christoffersen; stress test 2008, 2020, 2022.
  5. Ba mục tiêu: thành thạo quy trình đo lường rủi ro thị trường; đánh giá độ tin cậy mô hình bằng kiểm định thống kê; khuyến nghị lựa chọn mô hình cho nhà quản trị rủi ro.
- Ghi chú lớp ("Mô hình 3 – BTH"): chuỗi thời gian; kiểm định rủi ro thị trường năm **2018, 2020, 2022**; mục tiêu thành thạo quy trình đo lường và **đánh giá mức độ rủi ro của thị trường**.
- Rubric: tổng quan tài liệu 15% (≥ 5 bài, có bài nền tảng) · dữ liệu & **tái lập** 20% (GitHub, requirements.txt, notebook chạy trọn vẹn) · phương pháp & **kiểm định giả định, có mô hình đối chứng** 25% · **diễn giải kinh tế–tài chính** 25% · thuyết trình & phản biện 15%.
- Ngày 7 có **vấn đáp trực tiếp trên code**: mọi thành viên phải giải thích được từng dòng.
- Nhóm phải nộp **nhật ký sử dụng AI**.

## 2. Thiết kế nghiên cứu của nhóm (ĐÃ CHỐT — mọi phân tích phải phục vụ phần này)

**Câu hỏi nghiên cứu trung tâm:**
> Việc phân bổ một phần danh mục từ VN-Index sang S&P 500 có giúp nhà đầu tư Việt Nam giảm rủi ro tổn thất lớn không, và lợi ích đó thay đổi thế nào trong các giai đoạn thị trường căng thẳng?

| # | Mục tiêu | Biến sử dụng | Câu hỏi cần trả lời |
|---|---|---|---|
| MT1 | Ước lượng rủi ro danh mục Việt–Mỹ bằng HS, tham số, Monte Carlo, GARCH(1,1) | r_VN; r_SP quy đổi VND; tỷ trọng → VaR, ES 97,5% | Danh mục kết hợp có rủi ro thấp hơn 100% VN không? Các phương pháp chênh nhau bao nhiêu? |
| MT2 | Đo lợi ích đa dạng hóa theo thời gian | Tương quan trượt VN–SP; mức giảm ES khi thêm S&P | Khi tương quan tăng, lợi ích giảm rủi ro có suy yếu không? |
| MT3 | Vai trò tỷ giá và bối cảnh lạm phát VN | Δ USD/VND; lạm phát tính từ CPI; ES danh mục | Lợi ích S&P còn giữ được sau quy đổi VND không? Rủi ro khác nhau thế nào giữa lạm phát thấp và cao? (**so sánh theo bối cảnh, KHÔNG kết luận nhân quả**) |
| MT4 | Kiểm định độ tin cậy dự báo VaR/ES | VaR/ES dự báo; lỗ thực tế; số lần và mức vượt | Kupiec (tần suất), Christoffersen (tính độc lập/dồn cụm), kiểm định riêng cho ES |
| MT5 | Stress test 2008, 2018, 2020, 2022 | VaR, ES, tương quan, số lần vượt trong từng giai đoạn | Mô hình nào đánh giá thiếu rủi ro khi khủng hoảng? |

**Ràng buộc thiết kế:**
- Mô hình **chỉ dùng đúng 2 file clean** (riêng `data/fred/SP500.csv` chỉ để đối chiếu giá S&P 500 với FRED, bảng T0b): `data/clean/cleaned_daily_data.csv` (VN-Index, S&P 500, USD/VND) và `data/clean/cleaned_cpi_inflation.csv` (CPI/lạm phát). Không nạp file raw hay nguồn bổ sung.
- CPI chỉ dùng để **tính lạm phát**, chỉ để **chia bối cảnh**; không đi vào VaR hằng ngày.
- **3 danh mục chính cố định:** 100% VN · 50/50 · 100% S&P.
- **Lưới tỷ trọng Application:** 100/0, 75/25, 50/50, 25/75, 0/100. **KHÔNG giải bài toán tối ưu.**
- Khuyến nghị cuối **định tính**, không nêu % cụ thể, chỉ khi mô hình đo đã vượt backtest.
- Khoảng thời gian của hai file hiện tại: giá ngày 07/02/2006–28/02/2025; CPI/lạm phát 01/2006–07/2026. Kiểm tra ngày thực tế khi thay file.

## 3. Nguyên tắc tối thượng

1. **Không look-ahead bias.** VaR/ES cho ngày t+1 chỉ dùng dữ liệu đến hết ngày t.
2. **Không bịa** số liệu, trích dẫn, p-value, DOI. Tài liệu chưa kiểm chứng ghi `[CITE — cần kiểm tra]`.
3. **Tái lập 100%:** seed cố định, tham số lấy từ `config.yaml`, không tương tác, một lệnh chạy toàn bộ.
4. **Đúng trước, đẹp sau.** Mỗi công thức có unit test với giá trị biết trước.
5. **Không nhân quả hóa** MT2, MT3: dùng "đi kèm với", "trùng với".
6. **Hỏi trước khi xóa** dữ liệu thô hoặc đổi cấu trúc lớn.
7. Kết quả bất thường thì **dừng lại và báo cáo**, không "sửa cho đẹp".

## 4. Quy ước bắt buộc

| Vấn đề | Quy ước |
|---|---|
| Thứ tự thời gian | Luôn **tăng dần**. Index là `DatetimeIndex` tên `Date`. |
| Lợi suất tài sản | Log return `r_t = ln(P_t/P_{t−1})` |
| S&P quy đổi VND | `r_SP_VND = r_SP_USD + r_USDVND` |
| Lợi suất danh mục | `R_p = Σ w_i (e^{r_i} − 1)`, `r_p = ln(1+R_p)` (tái cân bằng hằng ngày) |
| ES danh mục | Tính trên **chuỗi lợi suất danh mục** |
| Dấu VaR/ES | Số dương = mức lỗ |
| Vi phạm | `I_{t+1} = 1` nếu `r_{t+1} < −VaR_t` |
| Mức tin cậy | ES 97,5% (chính). VaR 95%, 97,5%, 99%. Kết luận backtest ở VaR 99%. |
| Cửa sổ rolling | 252 (mặc định), robustness 500 và 1000 |
| Lạm phát | `π_t = I_t / I_{t−12} − 1`, I là CPI IMF IFS (2010 = 100) |
| Seed | `SEED = 2026` |

## 5. Kiến trúc thư mục — xem README.md

## 6. Phong cách code

- Python ≥ 3.10, type hints, docstring tiếng Việt chuẩn NumPy, có công thức và tài liệu gốc.
- Tên biến tiếng Anh, bình luận tiếng Việt. `logging` thay `print` trong `src/`.
- `ruff` và `pytest` sạch trước khi báo xong một phase.

## 7. Quy trình làm việc

1. Cuối phase: chạy test, đối chiếu tiêu chí nghiệm thu, nêu MT được trả lời.
2. Commit `phase-N: <mô tả>`.
3. Cập nhật `docs/ai_usage_log.md`.

## 8. Quyết định đã chốt ở Phần 0 (30/09/2026)

| # | Vấn đề | Quyết định | Lý do |
|---|---|---|---|
| Q1 | Giai đoạn stress | 2008 (GFC), 2018 (thương mại Mỹ–Trung), 2020 (COVID), 2022 (thắt chặt/lạm phát); 2011–12 là mở rộng | Đề yêu cầu 2008/2020/2022; ghi chú lớp yêu cầu 2018/2020/2022 → lấy hợp |
| Q2 | Tỷ giá | Dùng USD/VND từ file giá clean trong `data/clean`; lọc 3 điểm lỗi báo giá bằng Hampel 1 vòng (`T0_fx_cleaning_log`) | Luồng chỉ dùng file clean; điểm lỗi làm méo lợi suất S&P quy đổi VND |
| Q3 | CPI | CPI Việt Nam từ IMF IFS (tháng, 2010 = 100) trong file clean thứ hai; code kiểm tra cột lạm phát khớp CPI_t/CPI_(t−12) − 1 | Một nguồn chuẩn quốc tế, có đến 07/2026 |
| Q4 | Ngưỡng lạm phát | 4% (≈ trung vị 3,94%, gần mục tiêu điều hành); robustness trung vị, tam phân vị | |
| Q5 | Mô hình VAR (Bài 9) | Thêm VAR–Granger–IRF cho VN–S&P–tỷ giá (mô tả lan tỏa) | Gắn với nội dung môn |
| Q6 | Kho mã | git cục bộ; nhóm tự đẩy lên GitHub | |
| Q7 | Phạm vi | Chỉ bốn phương pháp VaR/ES: HS, Normal, MC_Normal, GARCH_N (GARCH(1,1)-Normal); giữ các kiểm định/backtest và phân tích MT1–MT5, không chạy biến thể mô hình ngoài đề | Thu hẹp theo yêu cầu đề án |
| Q8 | Chạy lại cho người không biết code | Nhấp đúp `CHAY_DU_AN.bat` để tự cài môi trường (nếu cần) và mở dashboard; trong dashboard bấm Chạy phân tích → Bắt đầu chạy toàn bộ. Kiểm tra tái lập chỉ hợp lệ với bộ tham chiếu tạo từ hai file clean hiện tại | Thầy cử người ít biết code chạy lại |
