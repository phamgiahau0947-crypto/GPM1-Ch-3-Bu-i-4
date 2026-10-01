# Bản nháp báo cáo — Đề án 03: Đo lường rủi ro thị trường: VaR, ES và kiểm định ngược

> Mọi con số lấy từ `outputs/tables/` của lần chạy đầy đủ gần nhất (`python scripts/run_all.py all`); công thức ở
> `docs/methodology.md`. Nhóm cần đọc lại, chỉnh văn phong và bổ sung trích dẫn trước khi nộp bản cuối.

## 1. Tóm tắt

Câu hỏi: phân bổ một phần danh mục từ VN-Index sang S&P 500 (quy đổi VND) có giúp nhà đầu tư Việt Nam giảm rủi ro tổn thất lớn
không, và lợi ích đó thay đổi thế nào trong các giai đoạn căng thẳng? Dữ liệu ngày 02/2006–02/2025 (4.610 phiên), 3 danh mục
(100% VN · 50/50 · 100% S&P), bốn phương pháp theo đề (mô phỏng lịch sử HS, tham số Normal, Monte Carlo, GARCH(1,1)), dự báo
cuốn chiếu 252 phiên, ES 97,5% theo FRTB, kiểm định Kupiec và Christoffersen, stress test 2008, 2018, 2020, 2022.

- Danh mục 50/50 có ES 97,5% thấp hơn 100% VN ở **cả 4 phương pháp**, mức giảm trung vị **32,7%** (30,6–34,1%).
- Với cửa sổ 252 phiên, **không phương pháp nào vượt qua đồng thời Kupiec và Christoffersen ở VaR 99%**: các mô hình giả định
  phân phối chuẩn vi phạm gấp khoảng 2–3 lần kỳ vọng; HS có tần suất vi phạm gần đúng nhất nhưng vi phạm dồn cụm. Chỉ HS với cửa
  sổ 500–1000 phiên qua được cả hai kiểm định (100% VN).
- Lợi ích đa dạng hóa thu hẹp khi tương quan VN–Mỹ tăng (DR 29,6% → 24,3%, p = 0,015) và trong khủng hoảng các mô hình
  phân phối chuẩn đánh giá thiếu rủi ro nặng nhất (Normal vi phạm VaR99 gấp 9,0 lần kỳ vọng).

## 2. Dữ liệu và phương pháp

- **Dữ liệu:** giá đóng cửa ngày VN-Index (HOSE), S&P 500 (USD) và tỷ giá giao dịch USD/VND từ Investing.com, 07/02/2006–28/02/2025;
  CPI Việt Nam theo tháng từ IMF International Financial Statistics (IFS), chỉ số gốc 2010 = 100, dùng để tính lạm phát so cùng kỳ.
  Giá S&P 500 khớp chuỗi FRED `SP500` tới 0,0024% (T0b) trên 2.036 phiên trùng (từ 30/09/2016). Tỷ giá có 3 điểm lỗi báo giá (tháng
  12/2009, giá lệch rồi quay về ngay) được lọc bằng bộ lọc Hampel và ghi lại ở `T0_fx_cleaning_log`.
- **Lợi suất:** log return; $r^{SP,VND}=r^{SP,USD}+r^{USDVND}$; danh mục tái cân bằng ngày cộng lợi suất đơn có trọng số.
- **Mô hình:** HS, Normal, Monte Carlo (10.000 đường, seed 2026), GARCH(1,1)-Normal (Bollerslev 1986, ước lượng lại mỗi 20 phiên).
  Dự báo cho ngày $t+1$ chỉ dùng dữ liệu đến $t$ (test `test_no_lookahead`). Mẫu so sánh chung: 13/02/2007–28/02/2025, 4.357 ngày.
- **Kiểm định:** Kupiec (1995) cho tần suất vi phạm; Christoffersen (1998) cho tính độc lập và bao phủ có điều kiện; mức 5%.

## 3. Kết quả

### 3.1 Đặc điểm dữ liệu và kiểm định giả định (T1, T2)

Độ biến động năm: VN-Index 23,0%, S&P 500 (VND) 20,1%, danh mục 50/50 15,5%. Mọi chuỗi lệch trái và có đuôi dày (độ nhọn vượt:
VN 2,8; S&P 11,9). Jarque–Bera bác bỏ phân phối chuẩn ở **5/5 chuỗi** → giả định của Normal và Monte Carlo không được dữ liệu ủng
hộ. ARCH-LM(10) và Ljung–Box trên $r^2$ có ý nghĩa ở VN, S&P và danh mục 50/50 (không có ở USD/VND, chuỗi được quản lý) → biến
động theo cụm, là căn cứ dùng GARCH(1,1). ADF và KPSS cùng xác nhận lợi suất dừng. GARCH của VN-Index có $\alpha+\beta=0{,}986$,
half-life khoảng 49 phiên (T3).

### 3.2 MT1 — Rủi ro danh mục theo bốn phương pháp (T4)

ES 97,5% trung bình mỗi ngày (mẫu chung):

| Mô hình | 100% VN | 50/50 | 100% S&P (VND) |
|---|---|---|---|
| HS | 3,73% | 2,59% | 3,28% |
| Normal | 3,16% | 2,12% | 2,69% |
| Monte Carlo | 3,17% | 2,13% | 2,70% |
| GARCH(1,1) | 2,97% | 1,96% | 2,42% |

Danh mục 50/50 luôn rủi ro thấp nhất; chênh lệch giữa mô hình cao nhất và thấp nhất tới 0,75 điểm %/ngày (100% VN), tức lựa chọn
mô hình quan trọng không kém lựa chọn tỷ trọng. Normal và Monte Carlo gần như trùng nhau (Monte Carlo chỉ thêm sai số mô phỏng).

### 3.3 MT4 — Độ tin cậy của dự báo (T5)

Số vi phạm VaR 99% trên 4.357 ngày (kỳ vọng 43,6):

| Mô hình | 100% VN | 50/50 | 100% S&P |
|---|---|---|---|
| HS | 54 | 62 | 84 |
| Normal | 90 | 96 | 133 |
| Monte Carlo | 90 | 95 | 133 |
| GARCH(1,1) | 99 | 106 | 123 |

Không mô hình nào được cả hai kiểm định ủng hộ ở VaR 99%. HS cho 100% VN qua Kupiec (p = 0,126) nhưng bị Christoffersen bác bỏ
(p_cc < 0,001): tổng số vi phạm hợp lý nhưng vi phạm dồn thành cụm vì cửa sổ lịch sử phản ứng chậm. Normal, Monte Carlo và
GARCH-Normal vi phạm quá nhiều: giả định đổi mới chuẩn bỏ qua đuôi dày đã thấy ở T2. Robustness (T13, 70 cấu hình): chỉ **HS với
cửa sổ dài hơn** cho 100% VN qua được cả hai kiểm định (500 phiên: 42 vi phạm, tỷ lệ 1,02%; 1000 phiên: 35 vi phạm, 0,97%) — cửa sổ
dài chứa nhiều cú sốc hơn nên VaR ít bị "quên" rủi ro sau giai đoạn yên ổn. Đổi tần suất ước lượng lại GARCH hay dùng dữ liệu lệch pha
không thay đổi kết luận.

### 3.4 MT2 — Đa dạng hóa theo thời gian (T8)

Lợi ích đa dạng hóa tương đối (DR, GARCH) trung bình 29,6% khi tương quan 252 phiên ở tam phân vị thấp, còn 24,3% ở tam phân
vị cao (chênh −5,3 điểm %, p block bootstrap = 0,015). Tương quan khi cả hai thị trường cùng giảm mạnh (10% đuôi) là 0,13 so với
0,05 nếu lợi suất chuẩn (T8b). Với dữ liệu lệch pha, tương quan trong các giai đoạn stress 0,12–0,37 so với 0,19 lúc yên ổn; sau
hiệu chỉnh Forbes–Rigobon còn 0,06–0,26 (T8d). Đây là quan hệ mô tả ("đi kèm với"), không phải nhân quả.

### 3.5 MT3 — Tỷ giá và bối cảnh lạm phát (T9, T10, T16)

Quy đổi VND gần như không làm tăng rủi ro đuôi: ΔES do tỷ giá của 100% S&P chỉ −0,01 đến +0,03 điểm %/ngày tùy mô hình; tương
quan S&P (USD) với USD/VND ≈ 0; tỷ giá đóng góp −0,4% ES của danh mục 50/50 (hơi bù lỗ). Khi lạm phát > 4%, ES của 100% VN trung
bình 3,41% so với 2,55% khi lạm phát thấp (p < 0,001), nhưng DR không khác biệt (26,7% so với 25,7%, p = 0,53). Các tháng lạm phát
cao trùng với những cú sốc khác (2008, 2011, 2022) nên chỉ so sánh theo bối cảnh. VAR(1): S&P có thông tin dự báo cho VN-Index
(Granger F = 278, p ≈ 0), giải thích 6,7% phương sai sai số dự báo 10 ngày của VN; tỷ giá gần như không (0,1%).

### 3.6 MT5 — Stress test (T11, T12)

Trung bình qua 4 giai đoạn lõi và 3 danh mục, tỷ lệ vi phạm VaR99 gấp 9,0 lần kỳ vọng với Normal và 5,5 lần với GARCH(1,1).
COVID-19 với 100% S&P: Normal vi phạm 11/48 phiên (gấp 22,9 lần kỳ vọng) và mất 15 phiên để VaR tăng gấp đôi; GARCH chỉ 3 vi phạm
và phản ứng sau 1 phiên. Normal là mô hình "đánh giá thiếu rủi ro nhất" nhiều nhất (8 lần, T11b). Kịch bản giả định trên 1 tỷ VND:
VN −7% và S&P −10% làm danh mục 50/50 lỗ 8,5%; nếu đồng thời VND mất giá 5% thì chỉ lỗ 6,25% (tỷ giá đệm lỗ). Nếu tương quan tăng
lên 0,9, ES 97,5% của 50/50 tăng từ 2,29% lên 3,09% — gần bằng danh mục thuần, tức lợi ích đa dạng hóa gần như mất (T12).

### 3.7 Khuyến nghị (T14, T15, `docs/application_draft.md`)

Vì không mô hình nào vượt cả hai kiểm định, kết quả phân bổ chỉ mang tính **thăm dò**. Theo HS, tỷ trọng có ES thấp nhất là 50/50
cả toàn kỳ và lúc bình thường; 25/75 trong 2018 và 2022; 100% VN trong COVID-19 (cú sốc bắt nguồn từ Mỹ). Với giới hạn ES minh
họa 4%/ngày, không tỷ trọng nào thỏa trong mọi giai đoạn stress lõi (GFC 2008 vượt giới hạn ở mọi tỷ trọng).
Xếp hạng mô hình (T15): 1. HS · 2. GARCH(1,1) · 3. Monte Carlo · 4. Normal.

## 4. Trả lời ba mục tiêu của đề án

1. **Quy trình đo lường rủi ro thị trường:** dữ liệu → kiểm tra và làm sạch → kiểm định giả định → bốn phương pháp VaR/ES dự báo
   cuốn chiếu → backtest → stress test → khuyến nghị; một lệnh chạy toàn bộ, seed cố định, kiểm tra tái lập tự động.
2. **Độ tin cậy của mô hình:** với cấu hình chính (cửa sổ 252 phiên), cả bốn phương pháp đều chưa đạt ở VaR 99%. Nguồn gốc lỗi khác
   nhau: HS đúng về tần suất nhưng phản ứng chậm (vi phạm dồn cụm); Normal/Monte Carlo/GARCH-Normal sai về đuôi vì giả định chuẩn.
   HS với cửa sổ 500–1000 phiên là cấu hình duy nhất được cả hai kiểm định ủng hộ (100% VN).
3. **Khuyến nghị cho nhà quản trị rủi ro (định tính):** không dùng Normal hay Monte Carlo chuẩn một mình cho quyết định vốn; dùng HS
   với cửa sổ dài làm thước đo chính và GARCH(1,1) làm tín hiệu cảnh báo sớm khi biến động tăng; đọc kết quả cùng stress test. Thêm S&P 500 vào
   danh mục VN-Index giảm rủi ro đuôi đáng kể, nhưng lợi ích thu hẹp khi tương quan tăng và có thể đảo chiều khi cú sốc bắt nguồn
   từ Mỹ. Không nêu tỷ trọng % cụ thể.

## 5. Hạn chế

- Chỉ số không phải tài sản đầu tư trực tiếp; bỏ qua phí, thuế, hạn chế chuyển vốn của nhà đầu tư cá nhân Việt Nam.
- File dữ liệu chỉ giữ ngày cả hai thị trường cùng mở cửa (một số lợi suất VN là lợi suất 2 phiên); phiên Mỹ đóng cửa sau phiên VN
  (đã đối chiếu bằng dữ liệu lệch pha).
- Bốn phương pháp theo đề đều giả định phân phối chuẩn hoặc lịch sử lặp lại; phân phối đuôi dày hay EVT nằm ngoài phạm vi đề án
  và là hướng mở rộng tự nhiên từ kết quả backtest.
- Đề án không triển khai kiểm định riêng cho ES; lạm phát chỉ dùng để chia bối cảnh, không kết luận nhân quả.
