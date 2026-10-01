# Nhật ký sử dụng công cụ AI (bắt buộc nộp kèm)

> Công cụ: Claude Code (Anthropic, mô hình Claude Opus 5.5). Cột "Nhóm kiểm tra/sửa" và "Thành viên" do nhóm **tự điền** sau khi rà soát —
> AI không được điền thay. Mọi đoạn AI viết phải được một thành viên đọc, chạy lại và giải thích được khi vấn đáp.

| Ngày | Phase | AI làm gì | Nhóm kiểm tra / sửa gì | Thành viên chịu trách nhiệm |
|---|---|---|---|---|
| 30/09/2026 | 0 | Kiểm kê repo và 4 file dữ liệu; phát hiện lỗi parse ngày (28% dòng S&P/tỷ giá ghép sai), lỗi dữ liệu tỷ giá Yahoo, dạng CPI; đề xuất kế hoạch (ghi chép kiểm kê đã bỏ khỏi bản nộp) | | |
| 30/09/2026 | 1 | Viết `data_pipeline.py`, `inflation.py`, `portfolio.py`, `config.yaml`, `SOURCES.md`; bộ lọc làm sạch tỷ giá (Hampel) | | |
| 30/09/2026 | 2 | Viết `diagnostics.py` (JB, AD, ADF, KPSS, ARCH-LM, Ljung–Box, AIC/BIC, sign bias); sửa lỗi quy đổi log-likelihood | | |
| 30/09/2026 | 3–4 | Viết 14 mô hình trong `models/` và `rolling.py`; sửa khởi tạo phương sai GARCH cho khớp `arch` (test khớp 1e−6) | | |
| 30/09/2026 | 5 | Viết `backtest/` (Kupiec, Christoffersen, Basel, duration, Z2, McNeil–Frey, FZ0, DM, MCS) | | |
| 30/09/2026 | 6–7 | Viết `diversification.py` (sửa DCC kẹt cực trị địa phương bằng đa điểm khởi đầu), `fx_inflation.py`, `spillover.py` (VAR) | | |
| 30/09/2026 | 8–9 | Viết `stress.py`, `application.py`; chuyển các câu diễn giải viết cứng thành câu sinh tự động từ số liệu | | |
| 30/09/2026 | 1.6 | Tích hợp FRED theo yêu cầu đề: tải SP500, 2 chuỗi tỷ giá năm (Penn World Table); nối S&P FRED (2016→) với Yahoo (2006–2016); `fred_validation.py` (T0b–T0d, F0); chạy lại toàn bộ và cập nhật số liệu báo cáo | | |
| 30/09/2026 | 10–12 | `plots.py` (25 hình), `reporting.py`, notebook, dashboard, CI; soạn `methodology.md`, `viva_guide.md`, `report_draft.md`, `literature_review.md` | | |
| 30/09/2026 | Nhóm | (Thành viên nhóm) Thêm chế độ nạp dữ liệu sạch `data/cleaned/`, menu vận hành và chú thích giao diện; tải tỷ giá Investing và CPI IMF | | |
| 30/09/2026 | 13 | Tích hợp tỷ giá Investing (nối Yahoo) và CPI IMF (kéo dài 2026); sửa 3 lỗi (crash khi chuỗi sạch, thiếu import ROOT, đọc ngày file sạch); giao diện Streamlit nhiều trang; file .bat cài đặt/chạy/kiểm tra; script kiểm tra tái lập (281 chỉ tiêu + MD5); cập nhật báo cáo và cẩm nang theo số liệu mới; thử cài đặt và chạy lại trong thư mục sạch | | |
| 30/09/2026 | 14 | Đối chiếu lại toàn bộ yêu cầu slide đề: viết `requirements_check.py` (31 yêu cầu, bằng chứng số liệu → `docs/DOI_CHIEU_YEU_CAU.md`, trang "Đối chiếu yêu cầu đề"); thêm đối chiếu FRED độ biến động VN-Index (`DDSM01VNA066NWDB`, T0f); thiết kế lại giao diện theo phong cách ngân hàng (navy + vàng đồng, Montserrat/Be Vietnam Pro đóng gói sẵn, bảng màu biểu đồ kiểm định mù màu, tương phản WCAG AA — `docs/design_system.md`) | | |
| 30/09/2026 | Điều chỉnh nguồn | Đổi nguồn mặc định sang hai file clean trong `data/clean/`; bỏ đọc raw/FRED/IMF trong các bước clean-only; ghi nguồn vào dấu hoàn tất để giao diện không hiển thị nhầm kết quả cũ; cập nhật hướng dẫn, dashboard và kiểm tra tái lập | | |
| 30/09/2026 | Thu gọn luồng dữ liệu | Cố định loader giá/CPI vào hai file clean; báo lỗi nếu dữ liệu sai thứ tự, trùng ngày hoặc giá trị không hợp lệ thay vì tự sửa; xóa `data/raw/`, `data/cleaned/`, cache `data/processed/`, `Data PJ4/Data thô/`, script làm sạch và mã chạy legacy; giữ nguyên hai file clean và `outputs/`; kiểm thử 47 test, Ruff và health endpoint dashboard | | |
| 30/09/2026 | Đơn giản hóa cách chạy | Gộp hướng dẫn chạy vào README; thay nhiều launcher cài đặt/chạy riêng bằng `CHAY_DU_AN.bat` duy nhất (tự cài môi trường lần đầu rồi mở dashboard); trong dashboard bấm **Bắt đầu chạy toàn bộ** để chạy mô hình và backtest; cập nhật hướng dẫn UI, yêu cầu đề và cẩm nang vấn đáp | | |
| 30/09/2026 | Thu hẹp mô hình theo đề | Giới hạn registry, pipeline rolling, bảng, dashboard và notebook còn HS, Normal, MC_Normal, GARCH_N; loại bỏ biến thể ngoài phạm vi khỏi mã triển khai; thêm kiểm tra cấu hình mô hình vào dấu hoàn tất để không trình bày outputs cũ; đánh dấu bản nháp/báo cáo kết quả cũ cần cập nhật sau khi chạy lại | | |
| 30/09/2026 | Thu hẹp kiểm định | Xóa implementation ngoài phạm vi khỏi backtest; chỉ giữ Kupiec và Christoffersen cho VaR; gỡ ES backtest, Basel/duration, DM/FZ0/MCS và kiểm định giả định; đồng bộ dashboard, notebook, checklist, bảng báo cáo và test phụ thuộc | | |
| 30/09/2026 | Cải thiện trải nghiệm dashboard | Thêm trang hướng dẫn làm trang mở đầu; tự động đề xuất mô hình trong phân tích tỷ trọng tùy ý; tăng khoảng đệm tiêu đề; bỏ trang/step đối chiếu yêu cầu khỏi Streamlit và pipeline | | |
| 30/09/2026 | Làm rõ lựa chọn mô hình | Hiển thị rõ mức đạt Kupiec/Christoffersen của mô hình đứng đầu; cảnh báo khi không mô hình nào đạt, đồng thời giữ bản diễn giải thăm dò không bị hiểu nhầm là kết luận | | |
| 30/09/2026 | Rà soát trước khi nộp | Chạy lại toàn bộ từ đầu và đối chiếu từng bảng; bỏ 12 file kết quả cũ không còn được tạo (bảng FRED T0b–T0f, T9c cũ, báo cáo tái lập cũ); lọc 3 điểm lỗi báo giá tỷ giá 12/2009 (`clean_fx_spikes`, T0_fx_cleaning_log); thêm lại kiểm định giả định T2 (JB, AD, ADF, KPSS, ARCH-LM, Ljung–Box) theo rubric; sửa câu tự sinh sai ở MT5 (GFC 2008), cảnh báo lặp ở application_draft, half-life khi α+β ≈ 1; chuyển dấu hoàn tất ra `outputs/last_successful_run.json`; đổi thư mục dữ liệu thành `data/clean/`; thêm đối chiếu giá S&P 500 với chuỗi FRED SP500 lưu sẵn (`fred_sp500_check`, T0b, chỉ kiểm chứng); cập nhật methodology, viva_guide, report_draft, README theo số liệu mới; tạo lại bộ tham chiếu tái lập | | |
| 01/10/2026 | Ghi nguồn dữ liệu | Nhóm cung cấp nguồn: Investing.com (giá đóng cửa VN-Index, S&P 500, USD/VND) và IMF IFS (CPI tháng, 2010 = 100); AI cập nhật README, methodology, báo cáo, cẩm nang, tổng quan tài liệu, giao diện và chú thích hình; bỏ hàm xử lý CPI dạng cũ không còn dùng; thêm kiểm tra cột lạm phát khớp CPI_t/CPI_(t−12) − 1 khi nạp | | |

## Những điểm nhóm BẮT BUỘC tự kiểm tra
1. Tên tác giả, năm, số trang của mọi tài liệu đánh dấu [CITE] (V2–V5, LA1, LA2) — AI không được bịa.
2. Ngày tải hai file clean trong `data/clean/` (nguồn đã ghi: Investing.com cho giá ngày, IMF IFS cho CPI).
3. Điểm định tính (độ phức tạp, khả năng giải thích) trong `application.py` — là đánh giá của nhóm, cần thống nhất.
4. Chạy lại `python scripts/run_all.py all --fresh` trên máy nhóm và đối chiếu số trong báo cáo với `outputs/tables/`.
5. Nếu thay đổi một trong hai file clean, chạy lại toàn bộ phân tích và tạo lại bộ tham chiếu sau khi kiểm tra kết quả.

## Sự cố trong phiên làm việc (ghi nhận trung thực)
- Khi dừng tiến trình rolling chạy nền để chạy lại với code đã sửa, lệnh `taskkill /IM python.exe` đã dừng **mọi** tiến trình Python
  trên máy lúc đó (không chỉ tiến trình của đề án). Nếu thành viên có chương trình Python khác đang chạy lúc ~08:37 ngày 30/09/2026, cần chạy lại.
