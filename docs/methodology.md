# Phương pháp luận — Đề án 03: VaR, ES & Backtesting cho danh mục Việt–Mỹ

> Mọi tham số nằm trong `config.yaml`; các công thức chính có unit test trong `tests/`. Ký hiệu: $r_t$ log return ngày,
> $L_t=-r_t$ lỗ, $q$ mức tin cậy, $p=1-q$. **VaR và ES là số dương = mức lỗ.**

## 1. Dữ liệu (Phase 1 — `data_pipeline.py`, `inflation.py`, `portfolio.py`)

Mô hình chỉ dùng hai file trong `data/clean/`:

| File | Nguồn | Nội dung | Khoảng |
|---|---|---|---|
| `cleaned_daily_data.csv` | Investing.com | Giá đóng cửa ngày VN-Index (HOSE), S&P 500 (USD), tỷ giá giao dịch USD/VND — đã ghép cùng ngày | 07/02/2006 – 28/02/2025, 4.610 phiên |
| `cleaned_cpi_inflation.csv` | IMF International Financial Statistics (IFS) | CPI Việt Nam theo tháng, chỉ số gốc 2010 = 100, và lạm phát so cùng kỳ | 01/2006 – 07/2026 |

- **Kiểm tra toàn vẹn** (`validate`): ngày tăng dần, không trùng, giá dương và hữu hạn, không có ngày tương lai.
- **Đối chiếu nguồn đề án (FRED, `fred_sp500_check`, T0b):** so với chuỗi FRED `SP500` lưu ở `data/fred/SP500.csv` (chỉ để kiểm chứng), giá S&P 500 trong file clean khớp tới 0,0024% (chênh do làm tròn) trên
  2.036 phiên trùng từ 30/09/2016. FRED chỉ lưu S&P 500 10 năm gần nhất và không có VN-Index hay tỷ giá VND theo ngày, nên
  cả ba chuỗi giá ngày lấy từ Investing.com cho thống nhất một nguồn.
- **Lọc điểm lỗi báo giá tỷ giá** (`clean_fx_spikes`): bộ lọc Hampel $|\ln(S_t/\text{median}_{15})|>1{,}5\%$ với trung vị trượt
  15 phiên căn giữa, lọc **1 vòng**; điểm lỗi thay bằng giá hợp lệ liền trước. Bắt được 3 điểm giá lệch rồi quay về ngay
  (01/12/2009: 18.275 → 19.150 → 18.276; 08 và 09/12/2009), ghi ở `T0_fx_cleaning_log`. Các đợt điều chỉnh tỷ giá thật
  (26/11/2009, 11/02/2010, 11/02/2011 +6,1%) giữ mức mới nên không bị lọc; vòng lọc thứ hai sẽ bắt nhầm mức mới ngày 27/11/2009,
  vì vậy chỉ lọc 1 vòng. Test: `test_clean_fx_spikes_removes_reversal_keeps_devaluation`.
- **Cảnh báo biến động lớn** (`T0_top_moves`): 5 ngày VN-Index vượt 7% là lợi suất gộp 2 phiên, do file clean chỉ giữ ngày
  cả hai thị trường cùng mở cửa (ví dụ 24/11/2006, sau Lễ Tạ ơn ở Mỹ) — không phải lỗi dữ liệu.

**Lợi suất và danh mục.**
$$r^{SP,VND}_t=r^{SP,USD}_t+r^{USDVND}_t,\qquad R_{p,t}=\sum_i w_i\,(e^{r_{i,t}}-1),\quad r_{p,t}=\ln(1+R_{p,t}).$$
Cộng log return tỷ giá vì $P^{VND}=P^{USD}\cdot S$. Danh mục tái cân bằng hằng ngày phải cộng **lợi suất đơn** có trọng số.
Phiên bản **lệch pha**: phiên VN ngày $t$ ghép S&P phiên Mỹ gần nhất **trước** $t$ (phiên Mỹ đóng cửa sau phiên VN) — dùng cho
tương quan và robustness.

**Lạm phát.** $\pi_t=I_t/I_{t-12}-1$ với $I_t$ là CPI IMF IFS (2010 = 100); khi nạp, code kiểm tra cột `Inflation_YoY` của file khớp
công thức này (kiểm chứng: 12/2008 = 19,89%, khớp số công bố). Chế độ "Cao" nếu $\pi_t>4\%$ (≈ trung vị, gần mục tiêu điều hành); robustness: trung vị,
tam phân vị; bản "đã công bố" dùng $\pi_{t-1}$. CPI **không** đi vào VaR ngày, chỉ để chia bối cảnh.

## 2. Thống kê mô tả và kiểm định giả định (Phase 2 — `descriptive.py`)

T1: trung bình, độ lệch chuẩn (năm hóa ×252, ×√252), độ lệch, độ nhọn vượt, phân vị đuôi — toàn kỳ và từng giai đoạn stress.
T2 kiểm tra giả định của các mô hình trên VN, S&P (USD), S&P (VND), USD/VND và danh mục 50/50:

| Kiểm định | H0 | Giả định được kiểm tra |
|---|---|---|
| Jarque–Bera, Anderson–Darling | phân phối chuẩn | Normal và MC_Normal giả định lợi suất chuẩn |
| ADF / KPSS | nghiệm đơn vị / chuỗi dừng | mô hình hóa trên lợi suất (chuỗi dừng) |
| ARCH-LM(5, 10) (Engle 1982) | không có hiệu ứng ARCH | lý do cần GARCH(1,1) |
| Ljung–Box Q(10) trên $r$ và $r^2$ | không tự tương quan | tính độc lập (HS, Normal) và cụm biến động |

Kết quả: phân phối chuẩn bị bác bỏ ở 5/5 chuỗi; ARCH-LM(10) có ý nghĩa ở 4/5 chuỗi → Normal và MC_Normal có cơ sở đánh giá thấp
rủi ro đuôi, GARCH có căn cứ; HS (không giả định phân phối) là **mô hình đối chứng** (`benchmark_model: HS`).

## 3. Bốn phương pháp VaR/ES theo đề (`models/`)

Chữ ký thống nhất `forecast(window, var_levels, es_level) -> {VaR_95, VaR_975, VaR_99, ES_975, params}`.

| Mô hình | Công thức | Giả định chính |
|---|---|---|
| HS — Mô phỏng lịch sử | $\text{VaR}_q=-\hat Q_{p}(r)$ (nội suy tuyến tính, Hyndman–Fan loại 7); $\text{ES}_q=-\overline{r\,\vert\,r\le \hat Q_p}$ | W phiên quá khứ lặp lại |
| Normal — tham số | $\text{VaR}_q=-(\mu+\sigma z_p)$, $\text{ES}_q=-\mu+\sigma\,\varphi(z_q)/(1-q)$ | $r\sim N(\mu,\sigma^2)$ i.i.d. |
| MC_Normal — Monte Carlo | $N=10.000$ đường, seed 2026, $\tilde r_j=\hat\mu+\hat\sigma z_j$, VaR/ES thực nghiệm của mẫu mô phỏng | như Normal (thêm sai số mô phỏng nhỏ) |
| GARCH_N — GARCH(1,1) (Bollerslev 1986) | $\sigma^2_t=\omega+\alpha\varepsilon^2_{t-1}+\beta\sigma^2_{t-1}$, $\text{VaR}=-(\mu+\sigma_{t+1}z_p)$ | đổi mới chuẩn; biến động theo cụm |

ES 97,5% là chỉ tiêu chính theo FRTB (Basel 2019): dưới phân phối chuẩn tương đương VaR 99% nhưng nắm được độ lớn đuôi và dưới
cộng tính. Test giá trị biết trước: Normal VaR99 = 2,3263σ; ES97,5 = 2,3378σ. Half-life GARCH $=\ln 0{,}5/\ln(\alpha+\beta)$, vô
hạn khi $\alpha+\beta\approx1$ (trường hợp tỷ giá USD/VND được quản lý).

## 4. Dự báo cuốn chiếu (Phase 4 — `rolling.py`)

Tại ngày $t$ dùng $r_{t-W+1..t}$ ($W=252$; robustness 500 và 1000) dự báo cho $t+1$; vi phạm $I_{t+1}=\mathbb 1[r_{t+1}<-\text{VaR}_t]$.
GARCH_N ước lượng lại mỗi 20 phiên (robustness 1 và 5 phiên trên 2018–2022); giữa các lần, $\sigma$ cập nhật bằng đệ quy với khởi
tạo *backcast* như thư viện `arch` (test khớp $10^{-6}$). Không hội tụ, $\omega\le0$ hoặc $\alpha+\beta\ge1$ ⇒ giữ tham số cũ
(đếm ở `T4b_rolling_runtime`). **Không look-ahead:** `test_no_lookahead` thay $r_{t+1}$ bằng −90% và kiểm tra mọi dự báo lập đến
ngày $t$ không đổi. Chạy song song bằng `joblib`, cache parquet theo mã băm của chuỗi dữ liệu (đổi dữ liệu thì tự tính lại).

## 5. Kiểm định ngược (Phase 5 — MT4, `backtest/`)

- **Kupiec (1995)** — tần suất vi phạm: $LR_{uc}=-2\ln[(1-p)^{T-x}p^x]+2\ln[(1-\hat\pi)^{T-x}\hat\pi^x]\sim\chi^2(1)$, quy ước $0\ln0=0$.
- **Christoffersen (1998)** — độc lập và bao phủ có điều kiện: $LR_{ind}=-2[\ln L(\pi)-\ln L(\pi_{01},\pi_{11})]\sim\chi^2(1)$;
  $LR_{cc}=LR_{uc}+LR_{ind}\sim\chi^2(2)$.
- Áp dụng cho VaR 95%, 97,5% và 99%, mức ý nghĩa 5%. Mô hình "đạt" ở một danh mục khi **không bị bác bỏ bởi cả hai** kiểm định ở
  VaR 99% (`T5b_pass_table`). ES 97,5% được báo cáo như thước đo rủi ro; đề án không triển khai kiểm định riêng cho ES.

## 6. Đa dạng hóa (Phase 6 — MT2, mô tả, `diversification.py`)

Tương quan trượt 63/252 phiên, EWMA ($\lambda=0{,}94$), DCC(1,1) hai bước (Engle 2002, nhiều điểm khởi đầu).
$DB_t=\text{ES}_t(VN)-\text{ES}_t(50/50)$; $DR_t=1-\frac{\text{ES}_t(50/50)}{0{,}5\,\text{ES}_t(VN)+0{,}5\,\text{ES}_t(SP)}$.
So sánh theo tam phân vị tương quan: Welch, Mann–Whitney và **moving block bootstrap** (block 63) vì chuỗi tự tương quan; hồi quy
$DR_t=a+b\rho_t+e_t$ với sai số Newey–West — diễn giải "đi kèm với", không nhân quả. Tương quan đuôi (Longin–Solnik 2001) so với
mức Normal hàm ý; hiệu chỉnh Forbes–Rigobon (2002) $\rho^*=\rho/\sqrt{1+\delta(1-\rho^2)}$.
DR âm ở 0,49% số ngày vì ES ước lượng trên mẫu hữu hạn và mỗi danh mục có tham số riêng — được báo cáo, không "sửa".

## 7. Tỷ giá và lạm phát (Phase 7 — MT3, `fx_inflation.py`, `spillover.py`)

$\Delta\text{ES}_{FX}=\text{ES}(VND)-\text{ES}(USD)$ (bản USD ≈ phòng ngừa tỷ giá hoàn toàn). Component ES Euler (lịch sử):
$R_p=wR_{VN}+(1-w)[R_{SP}+R_{FX}+R_{SP}R_{FX}]$, $\text{CES}_i=-E[c_i\mid R_p\le\text{VaR}]$, $\sum_i\text{CES}_i=\text{ES}$.
So sánh theo chế độ lạm phát bằng block bootstrap; lợi suất thực tháng $r^{real}=r-\ln(1+\pi^{m})$. Robustness mẫu con từ 2014 (T9c).

**Mô hình VAR (Bài 9):** $Y_t=(r^{SP,USD},r^{USDVND},r^{VN})'$, chọn trễ theo BIC, kiểm tra ổn định, Granger (F), IRF trực giao
(Cholesky S&P → tỷ giá → VN), FEVD 10 ngày. Granger = "có thông tin dự báo", không phải nhân quả.

## 8. Stress test (Phase 8 — MT5, `stress.py`)

Giai đoạn: GFC 01/2008–03/2009 · VN 2011–2012 (mở rộng) · thương mại Mỹ–Trung 02–12/2018 · COVID 20/02–30/04/2020 · thắt chặt 2022.
Chỉ số: VaR/ES trung bình, lỗ tệ nhất, max drawdown, số vi phạm VaR99 và Kupiec, $UR_{VaR}=\hat\pi/1\%$,
$UR_{ES}=\overline{L/\text{ES}\mid L>\text{VaR}^{97,5}}$, độ trễ phản ứng (số phiên từ vi phạm đầu tiên đến khi VaR99 ≥ 2× mức lúc cú sốc).
Kịch bản giả định trên 1 tỷ VND (tái định giá đầy đủ): VND mất giá 5%; VN −7% và S&P −10%; cả ba cùng lúc; tương quan VN–S&P tăng
lên 0,9 (VaR/ES Normal, σ toàn kỳ và σ của GFC 2008). Robustness: $W$ = 500/1000, refit 1/5/20 phiên, dữ liệu lệch pha,
bản USD (T13).

## 9. Khuyến nghị (Phase 9 — `application.py`)

- **Mô hình dùng để kết luận:** mô hình không bị Kupiec và Christoffersen bác bỏ ở VaR 99% trong nhiều danh mục chính nhất. Nếu
  không mô hình nào đạt, bản nháp tự sinh ghi **CẢNH BÁO** và chỉ trình bày kết quả thăm dò (trường hợp của dữ liệu hiện tại).
- **Xếp hạng mô hình (T15):** thứ hạng theo số danh mục đạt hai kiểm định VaR 99% (60%), mức lệch tỷ lệ vi phạm khỏi kỳ vọng trong
  khủng hoảng $|UR_{VaR99}-1|$ (25%), độ đơn giản và dễ giải thích (15%, điểm định tính của nhóm).
- **Lưới tỷ trọng** 100/0 · 75/25 · 50/50 · 25/75 · 0/100 so với giới hạn ES minh họa 3/4/5% (T14, T14b); **không** tối ưu hóa,
  khuyến nghị cuối chỉ nêu định hướng, không nêu tỷ trọng %.

## 10. Các lựa chọn kỹ thuật và lý do

| Lựa chọn | Lý do |
|---|---|
| ES 97,5% làm chỉ tiêu chính | FRTB (Basel 2019); dưới cộng tính, nắm được độ lớn đuôi |
| $W=252$ mặc định | quy ước ngành; cửa sổ 500/1000 đối chiếu riêng (T13) |
| Refit GARCH mỗi 20 phiên | cân bằng tốc độ và độ chính xác; refit 1/5 phiên đối chiếu (T13) |
| Mean hằng số trong GARCH | đơn giản, theo đề; hạn chế: VN-Index có tự tương quan bậc 1 (Ljung–Box trên $r$, T2) |
| Block bootstrap | chuỗi DB/DR/ES tự tương quan mạnh — kiểm định i.i.d. sẽ phóng đại ý nghĩa |
| Lọc tỷ giá 1 vòng Hampel | vòng thứ hai bắt nhầm đợt điều chỉnh tỷ giá thật |
