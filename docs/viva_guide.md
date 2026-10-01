# Cẩm nang vấn đáp trên code (Ngày 7)

> Mỗi module: (1) giải thích bằng lời, (2) dòng code then chốt, (3) ví dụ số tính tay, (4) 5 câu hỏi kèm đáp án.
> Cuối file là **8 câu bắt buộc** và 3 câu bổ sung. Mọi số liệu dẫn từ `outputs/tables/` (dữ liệu 02/2006–02/2025).
> Phạm vi: bốn phương pháp theo đề (HS, Normal, MC_Normal, GARCH_N); backtest VaR bằng Kupiec và Christoffersen.

---

## 1. `data_pipeline.py` — đọc, làm sạch, ghép dữ liệu
**Bằng lời.** Đọc file `data/clean/cleaned_daily_data.csv` (giá VN-Index, S&P 500, USD/VND đã ghép cùng ngày), parse ngày theo
định dạng khai báo sẵn và kiểm tra toàn vẹn (tăng dần, không trùng, giá dương, không có ngày tương lai). Tỷ giá được lọc điểm lỗi
báo giá bằng bộ lọc Hampel (3 điểm, `T0_fx_cleaning_log`); thêm phiên bản lệch pha S&P t−1.

**Dòng then chốt.**
```python
dates = pd.to_datetime(df["Date"], format="%m/%d/%Y", errors="coerce")   # parse theo định dạng khai báo, không đoán
flag = np.log(clean / med).abs() > threshold                              # Hampel: lệch > 1,5% so với trung vị 15 phiên
out = pd.merge_asof(left, right, on="Date", direction="backward", allow_exact_matches=False)  # lệch pha S&P t−1
```
**Ví dụ số.** Tỷ giá ngày 30/11, 01/12, 02/12/2009: 18.275; 19.150; 18.276. Trung vị ≈ 18.276 ⇒ |ln(19.150/18.276)| = 4,7% > 1,5% ⇒ 19.150 là
báo giá lỗi, thay bằng 18.275 ⇒ lợi suất ≈ 0 thay vì +4,7% rồi −4,7%. Đợt phá giá thật 11/02/2011 (+6,1% rồi giữ mức mới)
không bị lọc vì trung vị cũng chuyển sang mức mới. Chỉ lọc 1 vòng: vòng thứ hai bắt nhầm mức mới sau đợt điều chỉnh 26/11/2009.

**Hỏi – đáp.**
1. *Vì sao không để pandas tự đoán ngày?* — File dạng tháng/ngày/năm; đoán sai (`dayfirst=True`) sẽ đọc 1/5/2006 thành 1 tháng 5 và ghép sai ngày.
2. *Vì sao không forward-fill ngày nghỉ?* — Tạo lợi suất 0 giả, làm VaR thấp đi và làm sai tương quan.
3. *Hampel dùng giá tương lai, có phải look-ahead?* — Chỉ dùng để **nhận diện lỗi dữ liệu** (tiền xử lý); giá giữ lại là giá gốc, dự báo VaR vẫn chỉ dùng dữ liệu đến t.
4. *VN-Index có ngày tăng 8,7% — lỗi dữ liệu?* — Không: file chỉ giữ ngày cả hai thị trường cùng mở cửa, nên sau ngày nghỉ của Mỹ lợi suất VN là lợi suất gộp 2 phiên (`T0_top_moves`).
5. *Bản lệch pha để làm gì?* — Phiên Mỹ ngày t đóng cửa sau phiên VN ngày t, nên tương quan cùng ngày bị chệch xuống; ghép S&P phiên t−1 cho tương quan sát thực hơn (T8c, T8d).

## 2. `inflation.py` — lạm phát từ CPI
**Bằng lời.** CPI lấy từ IMF IFS, đã là chỉ số gốc 2010 = 100, nên lạm phát so cùng kỳ là tỷ số với 12 tháng trước. Khi nạp,
code kiểm tra cột lạm phát có sẵn trong file khớp công thức này. Chia chế độ
Cao/Thấp theo ngưỡng 4%, gán cho từng ngày giao dịch (bản diễn giải: tháng hiện tại; bản đã công bố: tháng trước).

**Dòng then chốt.** `implied = cpi_idx / cpi_idx.shift(12) - 1` — so với cột `Inflation_YoY`, lệch là báo lỗi.

**Ví dụ số.** CPI 12/2008 = 88,87; 12/2007 = 74,12 ⇒ π = 88,87 / 74,12 − 1 = 19,89% (khớp số công bố).

**Hỏi – đáp.** (1) *"2010 = 100" nghĩa là gì?* — Mức giá trung bình năm 2010 quy về 100; chỉ số 180 (12/2022) nghĩa là giá cao hơn 80% so với 2010. (2) *Kiểm chứng?* — 12/2008 ra 19,89% khớp số công bố (test `test_cpi_imf_file_base_2010_and_known_inflation`). (3) *Vì sao ngưỡng 4%?* — Gần mục tiêu điều hành và gần trung vị 3,94% ⇒ hai nhóm cân. (4) *Bản "đã công bố" để làm gì?* — Tránh dùng CPI chưa công bố khi phân tích như một tín hiệu dự báo. (5) *Vì sao không đưa lạm phát vào VaR?* — Thiết kế: CPI chỉ để chia bối cảnh; tần suất tháng không khớp VaR ngày.

## 3. `portfolio.py` — lợi suất danh mục
**Bằng lời.** Log return từng tài sản; S&P quy đổi VND = log return S&P + log return tỷ giá; danh mục tái cân bằng ngày cộng
lợi suất đơn có trọng số rồi lấy log.

**Dòng then chốt.** `np.log1p(w_a * np.expm1(r_a) + w_b * np.expm1(r_b))`

**Ví dụ số.** VN −2%, S&P(VND) +1% (log). Lợi suất đơn −1,980%, +1,005% ⇒ 50/50: −0,4875% ⇒ log = −0,4887%. Cộng log trực tiếp: −0,5% (sai số nhỏ nhưng tích lũy).

**Hỏi – đáp.** (1) *Test đảm bảo gì?* — SP_VND khớp log(P·S) tới 1e−12; 100/0 trùng VN. (2) *Tái cân bằng ngày có thực tế?* — Là giả định chuẩn; hạn chế: bỏ qua phí. (3) *Tỷ giá tăng thì nhà đầu tư VN lãi hay lỗ phần S&P?* — Lãi (USD mạnh lên). (4) *Vì sao ES danh mục tính trên chuỗi danh mục?* — Để giữ phụ thuộc giữa hai tài sản. (5) *Bản "USD" là gì?* — S&P không quy đổi ≈ phòng ngừa tỷ giá hoàn toàn.

## 4. `descriptive.py` — thống kê mô tả và kiểm định giả định
**Bằng lời.** T1 mô tả phân phối lợi suất (trung bình, độ lệch chuẩn, độ lệch, độ nhọn, phân vị). T2 kiểm tra giả định của các mô
hình: Jarque–Bera/Anderson–Darling (chuẩn — giả định của Normal, MC_Normal), ADF/KPSS (tính dừng), ARCH-LM và Ljung–Box trên r²
(biến động theo cụm — lý do dùng GARCH).

**Kết quả.** Chuẩn bị bác bỏ ở 5/5 chuỗi; ARCH-LM(10) có ý nghĩa ở 4/5 chuỗi; lợi suất dừng ở 5/5 chuỗi.

**Hỏi – đáp.** (1) *Chuẩn bị bác bỏ thì sao vẫn dùng Normal?* — Đề yêu cầu phương pháp tham số; nhóm dùng nó làm chuẩn so sánh và
cho thấy hậu quả: Normal vi phạm VaR99 nhiều gấp ~2 lần kỳ vọng (T5). (2) *Vì sao cần cả ADF và KPSS?* — Hai giả thuyết H0 ngược
nhau; cùng kết luận "dừng" thì chắc chắn hơn. (3) *ARCH-LM có ý nghĩa nghĩa là gì?* — Cú sốc bình phương hôm qua dự báo được cú
sốc bình phương hôm nay ⇒ phương sai thay đổi theo thời gian ⇒ cần GARCH.

## 5. `models/` — bốn phương pháp VaR/ES
**Bằng lời.** HS, Normal, MC_Normal và GARCH_N nhận cửa sổ lợi suất và trả về VaR 95/97,5/99 cùng ES 97,5%.
Ba phương pháp đầu dùng thống kê lịch sử, giả định chuẩn hoặc mô phỏng chuẩn; GARCH_N cập nhật biến động có điều kiện.

**Dòng then chốt.**
```python
out = {level_key("VaR", q): -(mu + sigma * ppf(1 - q)) for q in var_levels}   # VaR dương = lỗ
x = np.concatenate([[s2_1], shock]); signal.lfilter([1.0], [1.0, -beta], x)    # đệ quy GARCH
```
**Ví dụ số.** μ = 0, σ = 1%: VaR99 Normal = 2,326%; ES97,5 = 2,338%. GARCH: ω = 0,02, α = 0,1, β = 0,88 (thang %),
ε = −3, σ² = 2 ⇒ σ²ₜ₊₁ = 0,02 + 0,9 + 1,76 = 2,68 ⇒ σ = 1,637% ⇒ VaR99 (Normal) ≈ 3,81%.

**Hỏi – đáp.** (1) *HS nội suy phân vị thế nào?* — `np.quantile` tuyến tính (Hyndman–Fan 7). (2) *ES HS 97,5% với 252 quan sát lấy mấy điểm?* — Các điểm ≤ phân vị 2,5% (≈ 6–7 điểm) ⇒ ES HS nhiễu. (3) *Monte Carlo khác công thức đóng?* — Hội tụ về công thức đóng khi số đường mô phỏng tăng; seed cố định để tái lập.

## 6. `rolling.py` — dự báo cuốn chiếu
**Bằng lời.** Duyệt t từ W−1 đến T−2: cửa sổ `r[t−W+1 : t+1]` (kết thúc ở t) dự báo cho t+1. GARCH ước lượng lại theo cấu hình,
cache theo hash dữ liệu + tham số.

**Dòng then chốt.** `w = r[t - window + 1: t + 1]` … `out[t + 1] = [...]`.

**Hỏi – đáp.** (1) *Chứng minh không look-ahead?* — Xem câu bắt buộc 6. (2) *Refit không hội tụ thì sao?* — Dùng tham số cũ, đếm vào `failures`. (3) *Vì sao không refit mỗi ngày?* — Tốn thời gian; chu kỳ refit được cấu hình để cân bằng độ cập nhật và thời gian chạy. (4) *Tỷ lệ NaN?* — Kiểm tra trong bảng chất lượng đầu ra. (5) *Cache có làm sai khi đổi tham số?* — Khóa cache gồm hash dữ liệu và cấu hình mô hình.

## 7. `backtest/` — kiểm định ngược
**Bằng lời.** Chỉ có hai kiểm định VaR: Kupiec kiểm tra tỷ lệ vi phạm có phù hợp mức danh nghĩa không; Christoffersen kiểm tra
tính độc lập của vi phạm và bao phủ có điều kiện. ES được báo cáo như thước đo rủi ro, không có kiểm định ES trong phạm vi này.

**Ví dụ số (Kupiec).** T = 250, x = 5, p = 1%: LR = −2[245 ln 0,99 + 5 ln 0,01] + 2[245 ln 0,98 + 5 ln 0,02] = 1,956 < 3,84 ⇒ không bác bỏ (test `test_kupiec_hand_example`).

**Hỏi – đáp.** (1) *Kích thước kiểm định Kupiec đúng không?* — Mô phỏng 10.000 chuỗi Bernoulli(1%): tỷ lệ bác bỏ nằm trong 3–7%. (2) *n11 = 0 thì LR_ind?* — Quy ước 0·ln0 = 0. (3) *Kupiec đạt nhưng Christoffersen bác bỏ nghĩa là gì?* — Tần suất tổng thể có thể phù hợp nhưng vi phạm phụ thuộc theo thời gian, không đáp ứng kiểm định độc lập.

## 8. `diversification.py` — MT2
**Bằng lời.** Đo tương quan theo thời gian và mức giảm ES khi thêm S&P; so sánh lợi ích giữa lúc tương quan thấp/cao; kiểm định
bằng block bootstrap vì dữ liệu tự tương quan.

**Ví dụ số.** ES(VN) = 3,0%, ES(S&P) = 3,0%, ES(50/50) = 2,1% ⇒ DB = 0,9 điểm %; DR = 1 − 2,1/3,0 = 30%.

**Hỏi – đáp.** (1) *DR có thể âm?* — Về lý thuyết không (ES dưới cộng tính), thực nghiệm 0,49% số ngày vì ước lượng mẫu hữu hạn. (2) *Vì sao block bootstrap?* — Bảo toàn tự tương quan trong khối 63 ngày. (3) *DCC khác tương quan trượt?* — Mô hình hóa động học tương quan trên phần dư GARCH; a + b = 0,993 (cùng ngày), 0,962 (lệch pha), T8c. (4) *Longin–Solnik cho thấy gì?* — Tương quan khi cùng giảm mạnh (10% đuôi) = 0,13 so với 0,05 nếu Normal (T8b). (5) *Forbes–Rigobon?* — Tương quan có điều kiện theo giai đoạn biến động cao bị chệch lên; sau hiệu chỉnh giảm.

## 9. `fx_inflation.py` & `spillover.py` — MT3 và VAR
**Bằng lời.** So sánh ES bằng VND và USD để tách vai trò tỷ giá; phân rã ES theo Euler; so sánh ES/lợi ích đa dạng hóa theo chế
độ lạm phát. VAR(1) (chọn theo BIC) kiểm tra S&P có dự báo được VN không.

**Ví dụ số (Euler, T9b).** ES toàn kỳ của 50/50 = 3,01%: VN đóng góp 54,5%, S&P (USD) 46,0%, tỷ giá −0,4% (tỷ giá hơi bù lỗ —
USD thường tăng nhẹ đúng những ngày tệ nhất).

**Hỏi – đáp.** (1) *ΔES_FX dương nghĩa là?* — Quy đổi VND làm ES cao hơn; toàn kỳ ΔES_FX của 100% S&P chỉ −0,01 đến +0,03 điểm %/ngày (T9) ⇒ tỷ giá gần như không làm tăng rủi ro đuôi. (2) *Vì sao ΔES_FX có thể âm?* — USD tăng khi S&P giảm có thể đệm lỗ quy đổi VND. (3) *Granger S&P → VN có ý nghĩa là nhân quả?* — Không, chỉ là có thông tin dự báo; chủ yếu do lệch giờ đóng cửa. (4) *Vì sao thứ tự Cholesky S&P trước?* — Thị trường toàn cầu, đóng cửa sau. (5) *DR cao hơn khi lạm phát cao?* — Chỉ diễn giải là trùng bối cảnh, không phải nhân quả.

## 10. `stress.py` — MT5
**Bằng lời.** Cắt dự báo theo giai đoạn khủng hoảng, đo tỷ lệ vi phạm so với kỳ vọng (UR), lỗ thực tế/ES, độ trễ phản ứng;
thêm kịch bản giả định và robustness.

**Ví dụ số.** COVID, 100% S&P, Normal: 11 vi phạm / 48 ngày = 22,9% ⇒ UR = 22,9 lần kỳ vọng; GARCH_N chỉ 3 vi phạm (UR = 6,25)
và phản ứng sau 1 phiên so với 15 phiên của Normal (T11).

**Hỏi – đáp.** (1) *Mô hình nào đánh giá thiếu nhất?* — Thường là Normal/MC_Normal (GFC 2008, thương mại 2018, COVID); GARCH_N sát kỳ vọng nhất ở nhiều giai đoạn (T11b). (2) *Vì sao HS phản ứng chậm?* — Cửa sổ lịch sử chứa dữ liệu yên ổn; VaR tăng khi các khoản lỗ lớn đi vào cửa sổ. (3) *VND mất giá 5% ảnh hưởng gì?* — Danh mục có S&P có lợi nhuận quy đổi dương nếu giá S&P không đổi. (4) *Tương quan tăng ảnh hưởng thế nào?* — Có thể làm giảm lợi ích đa dạng hóa; xem phân tích mô tả MT2. (5) *GARCH_N phản ứng biến động ra sao?* — Cập nhật phương sai có điều kiện từ cú sốc và phương sai kỳ trước.

## 11. `application.py` — phân bổ theo giới hạn ES
**Bằng lời.** Chỉ dùng mô hình không bị bác bỏ bởi cả Kupiec và Christoffersen ở VaR 99% làm ứng viên kết luận. So sánh ES của 5 tỷ trọng với giới
hạn 3/4/5%, kiểm tra tính nhất quán giữa giai đoạn bình thường và khủng hoảng; chấm điểm mô hình cho nhà quản trị.

**Hỏi – đáp.** (1) *Vì sao không tối ưu tỷ trọng?* — Xem câu bắt buộc 8. (2) *Tỷ trọng nào thỏa ES 4% cả lúc khủng hoảng?* — Đọc bảng T14b sau khi chạy pipeline. (3) *Điểm định tính từ đâu?* — Điểm độ phức tạp và khả năng giải thích là đánh giá của nhóm. (4) *Nếu không mô hình nào vượt?* — Đúng là trường hợp hiện tại: báo rõ không mô hình nào được cả hai kiểm định VaR 99% ủng hộ, kết quả tỷ trọng chỉ là thăm dò; không thay bằng tiêu chí khác. (5) *Vậy khuyến nghị cho nhà quản trị là gì?* — Xếp hạng T15: HS đứng đầu (tần suất vi phạm gần kỳ vọng nhất, dù vi phạm dồn cụm), GARCH_N thứ hai (phản ứng nhanh nhất trong khủng hoảng); robustness T13 cho thấy HS cửa sổ 500–1000 phiên là cấu hình duy nhất qua cả hai kiểm định (100% VN). Không dùng Normal/MC_Normal một mình vì đánh giá thiếu rủi ro đuôi.

---

## 8 câu hỏi bắt buộc

**1. Vì sao FRTB dùng ES 97,5% thay VaR 99%?** VaR chỉ là một phân vị — không nói gì về độ lớn lỗ vượt qua nó và không dưới
cộng tính (Artzner et al. 1999), nên có thể "phạt" đa dạng hóa. ES là trung bình lỗ trong đuôi, là thước đo nhất quán (coherent),
nắm được độ dày đuôi. Mức 97,5% được chọn để ES dưới Normal ≈ VaR 99% (2,338σ so với 2,326σ), giữ mức vốn tương đương nhưng nhạy hơn với đuôi dày.

**2. Vì sao cộng log return tỷ giá để quy đổi?** Giá S&P bằng VND = giá USD × tỷ giá. Log của tích = tổng các log ⇒
$r^{VND}=r^{USD}+r^{FX}$ chính xác (không xấp xỉ). Với lợi suất đơn thì phải nhân: $(1+R^{USD})(1+R^{FX})-1$.

**3. Vì sao ES danh mục không bằng tổng ES riêng lẻ?** ES dưới cộng tính: ES(A+B) ≤ ES(A) + ES(B); dấu bằng chỉ khi hai tài sản
đồng biến hoàn toàn (comonotonic). Ngày VN lỗ nặng không nhất thiết trùng ngày S&P lỗ nặng ⇒ ES 50/50 thấp hơn trung bình ES hai
danh mục thuần (DR trung bình 21–31% tùy mô hình và mức tương quan, T8). Vì vậy ES phải tính trên chuỗi lợi suất danh mục.

**4. Kupiec đạt nhưng Christoffersen bác bỏ nghĩa là gì?** Tổng số vi phạm đúng kỳ vọng nhưng chúng dồn cụm (vi phạm hôm nay làm
tăng xác suất vi phạm ngày mai) ⇒ mô hình phản ứng chậm với biến động mới. Ví dụ HS cho 100% VN: Kupiec p = 0,126 (đạt) nhưng
LR_ind p = 0,00004 (T5) — đúng dấu hiệu của mô hình phi điều kiện.

**5. α + β gần 1 nói lên điều gì?** Biến động rất bền: cú sốc tắt dần chậm. Half-life = ln 0,5 / ln(α + β): VN-Index α + β = 0,986
⇒ half-life ≈ 49 phiên (T3). Tỷ giá USD/VND có α + β ≈ 1 (IGARCH): cú sốc không tắt dần, phương sai không điều kiện không xác định —
phù hợp với tỷ giá được quản lý, thay đổi theo từng đợt điều chỉnh.

**6. Làm sao chứng minh không có look-ahead?** (a) Code: cửa sổ `r[t−W+1 : t+1]` kết thúc ở t, dự báo lưu vào dòng t+1;
(b) test `tests/test_rolling.py::test_no_lookahead`: thay r[t+1] bằng −90% ⇒ dự báo đến ngày t giữ nguyên, các dự báo tương lai mới bị ảnh hưởng;
(c) chế độ lạm phát có phiên bản "đã công bố" trễ 1 tháng.

**7. Vì sao lạm phát chỉ để chia bối cảnh mà không kết luận nhân quả?** Lạm phát cao trùng với các cú sốc khác (2008, 2011, 2022:
khủng hoảng toàn cầu, thắt chặt tiền tệ, giá hàng hóa). Không có biến công cụ hay thiết kế tự nhiên để tách tác động riêng; mẫu chỉ
có vài đợt lạm phát cao ⇒ số quan sát độc lập ít. Vì vậy chỉ nói "ES cao hơn **trùng với** lạm phát cao".

**8. Vì sao không khuyến nghị tỷ trọng % cụ thể?** (a) Thiết kế của nhóm cấm tối ưu tỷ trọng; (b) kết quả phụ thuộc mô hình, giai
đoạn (COVID ngược chiều) và giới hạn ES do nhà đầu tư tự chọn; (c) chỉ số không phải tài sản đầu tư trực tiếp, bỏ qua phí/thuế/hạn
chế chuyển vốn; (d) dữ liệu quá khứ. Con số % sẽ tạo ảo giác chính xác — chỉ nêu định hướng "nghiêng về phía Mỹ".

**9. (Bổ sung) Đề ghi nguồn FRED — nhóm dùng thế nào?** Pipeline chỉ đọc hai file clean trong `data/clean/`. Giá S&P 500 trong
file khớp chuỗi FRED `SP500` tới 0,0024% (T0b) trên 2.036 phiên trùng (từ 30/09/2016). FRED chỉ lưu S&P 500 10 năm gần nhất và không có
VN-Index hay tỷ giá VND theo ngày, nên cả ba chuỗi giá ngày lấy từ Investing.com cho thống nhất một nguồn, và dùng FRED để kiểm
chứng; CPI lấy từ IMF IFS (2010 = 100), chỉ dùng để phân loại bối cảnh.

**10. (Bổ sung) Làm sao người khác chạy lại và biết kết quả đúng?** Nhấp đúp `CHAY_DU_AN.bat` để cài môi trường `.venv` (nếu cần)
và mở dashboard; chọn **Vận hành → Chạy phân tích → Bắt đầu chạy toàn bộ**, sau đó **Kiểm tra tái lập**. Script
`scripts/verify_reproducibility.py` so các con số then chốt với bộ tham chiếu `outputs/reproducibility/tham_chieu.json` và mã
MD5 của đúng hai file clean ⇒ KHỚP / GẦN KHỚP / LỆCH. Tái lập được vì seed cố định 2026, mọi tham số ở `config.yaml`, không có bước
nhập tay, thư viện ghim phiên bản.

**11. (Bổ sung) Có những kiểm định thống kê nào?** Kiểm định giả định (T2): Jarque–Bera, Anderson–Darling, ADF, KPSS, ARCH-LM,
Ljung–Box. Kiểm định ngược VaR (T5): Kupiec (tần suất vi phạm) và Christoffersen (độc lập/bao phủ có điều kiện). ES 97,5% được báo
cáo như thước đo rủi ro, không có kiểm định riêng cho ES. `pytest` là test phần mềm (công thức có giá trị biết trước), không phải
kiểm định thống kê.
