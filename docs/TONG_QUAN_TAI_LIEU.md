# Tổng quan tài liệu & định hướng học thuật — Đề án 03

> Claude Code chỉ được trích dẫn từ danh sách này. Tài liệu nào chưa có ở đây thì ghi `[CITE]`.
> **Nhóm phải tự mở và kiểm tra từng tài liệu** (tên tác giả, năm, số trang) trước khi đưa vào báo cáo.

## 1. Về hướng của PGS.TS Nguyễn Anh Phong

PGS.TS Nguyễn Anh Phong là Trưởng khoa Tài chính – Ngân hàng UEL. Các nghiên cứu tìm được thuộc nhánh **thanh khoản – định giá tài sản** và **rủi ro doanh nghiệp**:
- Nguyễn Anh Phong (2012), tác động của thanh khoản đến suất sinh lời cổ phiếu niêm yết trên TTCK VN, *Tạp chí Phát triển Kinh tế*, 264(10), 33–39.
- Thầy hướng dẫn luận án về CEO tự tin quá mức, rủi ro kinh doanh và hiệu quả hoạt động doanh nghiệp niêm yết.

Tra cứu lại (30/09/2026) **không tìm thấy** luận án hay bài nào của thầy về VaR/ES/GARCH. Cách dùng: trích bài 2012 ở phần bối cảnh (đặc thù thanh khoản, chu kỳ bong bóng–hoảng loạn của TTCK VN) để biện minh cho đuôi dày và biến động theo cụm.

### 1b. Luận án / nghiên cứu trong nước gần đề (thay thế để "làm theo")

| # | Tài liệu | Dùng ở đâu | Trạng thái |
|---|---|---|---|
| LA1 | Hoàng Đức Mạnh. *Một số mô hình đo lường rủi ro trên thị trường chứng khoán Việt Nam*. Luận án tiến sĩ, Trường ĐH Kinh tế Quốc dân. | Khung "nhiều mô hình đo rủi ro + kiểm định" cho TTCK VN — MT1, MT4 | [CITE — cần kiểm tra năm, số trang] |
| LA2 | Luận án tiến sĩ của TS. Võ Thị Ngọc Trinh (UEL, ngành Tài chính – Ngân hàng), giảng viên soạn Bài 8 (ARIMA/GARCH) và Bài 9 (VAR) của môn học | Quy trình GARCH-family và VAR theo bài giảng | [CITE — cần hỏi đề tài cụ thể] |
| LA3 | Bài giảng Bài 8 "Mô hình ARIMA và GARCH-family" và Bài 9 "Mô hình VAR" (TS. Võ Thị Ngọc Trinh, UEL) | Quy trình: ADF → ACF → ARCH-LM → GARCH; VAR: ADF → chọn trễ (AIC/BIC/HQ) → Granger → IRF | Tài liệu môn học |

## 2. Hướng phát triển (khớp đề nhất)

| Trục | Bài "xương sống" | Dùng cho |
|---|---|---|
| Phương pháp so sánh mô hình VaR | Kuester, Mittnik & Paolella (2006); McNeil & Frey (2000) | Bối cảnh tổng quan; không phải kiểm định đang chạy |
| Bằng chứng Việt Nam | Lê Hải Trung & Nguyễn Thị Mai Trang (2020); Hoàng Đức Mạnh (LA1) | So sánh với nghiên cứu VN-Index trước đó |
| Liên kết VN–Mỹ & tương quan khủng hoảng | Longin & Solnik (2001); Forbes & Rigobon (2002); V3, V4 | MT2, MT5 |
| Ứng dụng phân bổ | Rockafellar & Uryasev (2000, 2002) | Application |
| Chuẩn mực quản lý | Basel (1996, 2019 — FRTB) | ES 97,5%; traffic light là tài liệu nền, không chạy trong backtest hiện tại |

**Khoảng trống:** nghiên cứu VaR ở Việt Nam chủ yếu đo riêng VN-Index/VN30. Đề án đo **ES của danh mục Việt–Mỹ quy đổi VND**,
backtest VaR bằng Kupiec và Christoffersen, stress test và lợi ích đa dạng hóa theo thời gian. (Nhóm cần kiểm tra lại trên Google Scholar trước khi khẳng định.)

> Các bài báo về phương pháp khác trong danh mục dưới đây là tài liệu tham khảo học thuật, không đồng nghĩa chúng được cài đặt.
> Phạm vi implementation hiện tại chỉ gồm bốn phương pháp VaR/ES (HS, Normal, MC_Normal, GARCH_N) và hai backtest VaR
> (Kupiec, Christoffersen); không có backtest ES hay kiểm định/xếp hạng thống kê giữa mô hình.

## 3. Tài liệu nền tảng quốc tế

| # | Tài liệu | Dùng ở đâu | Độ chắc |
|---|---|---|---|
| 1 | Artzner, P., Delbaen, F., Eber, J.-M., & Heath, D. (1999). Coherent measures of risk. *Mathematical Finance*, 9(3), 203–228. | Vì sao ES tốt hơn VaR | Cao |
| 2 | Acerbi, C., & Tasche, D. (2002). On the coherence of expected shortfall. *Journal of Banking & Finance*, 26(7), 1487–1503. | Định nghĩa ES | Cao |
| 3 | Engle, R. F. (1982). Autoregressive conditional heteroscedasticity… *Econometrica*, 50(4), 987–1007. | ARCH, ARCH-LM | Cao |
| 4 | Bollerslev, T. (1986). Generalized autoregressive conditional heteroskedasticity. *Journal of Econometrics*, 31(3), 307–327. | GARCH(1,1) | Cao |
| 5 | Glosten, L., Jagannathan, R., & Runkle, D. (1993). *Journal of Finance*, 48(5), 1779–1801. | GJR-GARCH | Cao |
| 6 | Kupiec, P. (1995). Techniques for verifying the accuracy of risk measurement models. *Journal of Derivatives*, 3(2), 73–84. | Kupiec | Cao |
| 7 | Christoffersen, P. (1998). Evaluating interval forecasts. *International Economic Review*, 39(4), 841–862. | Christoffersen | Cao |
| 8 | Boudoukh, J., Richardson, M., & Whitelaw, R. (1998). The best of both worlds. *Risk*, 11(5), 64–67. | Age-weighted HS | Trung bình |
| 9 | Barone-Adesi, G., Giannopoulos, K., & Vosper, L. (1999). VaR without correlations for portfolios of derivative securities. *Journal of Futures Markets*, 19(5), 583–602. | Filtered HS | Trung bình |
| 10 | McNeil, A. J., & Frey, R. (2000). Estimation of tail-related risk measures for heteroscedastic financial time series: an extreme value approach. *Journal of Empirical Finance*, 7(3–4), 271–300. | GARCH-EVT, backtest ES | Cao |
| 11 | Rockafellar, R. T., & Uryasev, S. (2000). Optimization of conditional value-at-risk. *Journal of Risk*, 2(3), 21–41. | Application | Cao |
| 12 | Rockafellar, R. T., & Uryasev, S. (2002). Conditional value-at-risk for general loss distributions. *Journal of Banking & Finance*, 26(7), 1443–1471. | Application | Cao |
| 13 | Engle, R. (2002). Dynamic conditional correlation. *Journal of Business & Economic Statistics*, 20(3), 339–350. | DCC — MT2 | Cao |
| 14 | Longin, F., & Solnik, B. (2001). Extreme correlation of international equity markets. *Journal of Finance*, 56(2), 649–676. | Tương quan đuôi — MT2 | Cao |
| 15 | Forbes, K., & Rigobon, R. (2002). No contagion, only interdependence. *Journal of Finance*, 57(5), 2223–2261. | Độ chệch tương quan có điều kiện | Cao |
| 16 | Christoffersen, P., & Pelletier, D. (2004). Backtesting value-at-risk: A duration-based approach. *Journal of Financial Econometrics*, 2(1), 84–108. | Duration test | Cao |
| 17 | Engle, R., & Manganelli, S. (2004). CAViaR. *Journal of Business & Economic Statistics*, 22(4), 367–381. | CAViaR | Cao |
| 18 | Kuester, K., Mittnik, S., & Paolella, M. (2006). Value-at-risk prediction: A comparison of alternative strategies. *Journal of Financial Econometrics*, 4(1), 53–89. | Khung so sánh mô hình | Cao |
| 19 | Hansen, P., Lunde, A., & Nason, J. (2011). The model confidence set. *Econometrica*, 79(2), 453–497. | MCS | Cao |
| 20 | Acerbi, C., & Szekely, B. (2014). Backtesting expected shortfall. *Risk*, December. | Backtest ES | Trung bình |
| 21 | Patton, A., Ziegel, J., & Chen, R. (2019). Dynamic semiparametric models for expected shortfall (and value-at-risk). *Journal of Econometrics*, 211(2), 388–413. | FZ0 loss | Cao |
| 22 | Basel Committee on Banking Supervision (1996). Supervisory framework for the use of "backtesting" in conjunction with the internal models approach to market risk capital requirements. | Traffic light | Cao |
| 23 | Basel Committee on Banking Supervision (2019). Minimum capital requirements for market risk (FRTB). | ES 97,5% | Cao |
| 24 | Jorion, P. (2006). *Value at Risk: The New Benchmark for Managing Financial Risk* (3rd ed.). McGraw-Hill. | Giáo trình | Cao |
| 25 | Diebold, F. X., & Mariano, R. S. (1995). Comparing predictive accuracy. *Journal of Business & Economic Statistics*, 13(3), 253–263. | Kiểm định DM | Cao |
| 26 | Engle, R. F., & Ng, V. K. (1993). Measuring and testing the impact of news on volatility. *Journal of Finance*, 48(5), 1749–1778. | Sign bias test | Cao |
| 27 | Sims, C. A. (1980). Macroeconomics and reality. *Econometrica*, 48(1), 1–48. | Mô hình VAR | Cao |
| 28 | Granger, C. W. J. (1969). Investigating causal relations by econometric models and cross-spectral methods. *Econometrica*, 37(3), 424–438. | Granger causality | Cao |
| 29 | Riskmetrics Group / J.P. Morgan (1996). *RiskMetrics — Technical Document* (4th ed.). | EWMA λ = 0,94 | Cao |
| 30 | Cornish, E. A., & Fisher, R. A. (1938). Moments and cumulants in the specification of distributions. *Revue de l'Institut International de Statistique*, 5(4), 307–320. | Modified VaR | Cao |

### 3b. Ba bài nền tảng đề án chỉ định — đã dùng ở đâu

| Bài | Dùng trong code | Bảng/hình |
|---|---|---|
| Bollerslev (1986) — GARCH(1,1) | `src/market_risk/models/garch.py` (GARCH_N với đổi mới chuẩn) | T3, T4, F13 |
| Kupiec (1995) — POF test | `backtest/var_tests.py::kupiec` (+ test kích thước 10.000 mô phỏng, đối chiếu vùng không bác bỏ của Jorion) | T5, F9, F14 |
| Christoffersen (1998) — độc lập & bao phủ có điều kiện | `backtest/var_tests.py::christoffersen` (LR_ind, LR_cc) | T5, F14 |

### 3c. Nguồn dữ liệu (trích dẫn chuẩn)

| # | Nguồn | Ghi chú |
|---|---|---|
| D1 | S&P Dow Jones Indices LLC, *S&P 500* [SP500], retrieved from FRED, Federal Reserve Bank of St. Louis; https://fred.stlouisfed.org/series/SP500 (truy cập 30/09/2026) | đối chiếu giá S&P 500 trong file clean: khớp tới 0,0024% trên 2.036 phiên từ 30/09/2016 (T0b; file lưu ở `data/fred/SP500.csv`) |
| D2 | Investing.com — giá đóng cửa ngày VN-Index (HOSE), S&P 500 và tỷ giá giao dịch USD/VND (`data/clean/cleaned_daily_data.csv`) | [CITE — nhóm ghi nguồn gốc từng cột và ngày tải] |
| D3 | International Monetary Fund, *International Financial Statistics (IFS)* — Consumer Price Index, Viet Nam, tần suất tháng, 2010 = 100 (`data/clean/cleaned_cpi_inflation.csv`) | [CITE — nhóm ghi ngày truy cập] |

## 4. Tài liệu Việt Nam / VN–Mỹ (BẮT BUỘC kiểm tra lại)

| # | Tài liệu | Ghi chú |
|---|---|---|
| V1 | Lê Hải Trung & Nguyễn Thị Mai Trang (2020). *Các phương pháp đo lường giá trị chịu rủi ro: Ứng dụng cho thị trường Việt Nam* [tên đầy đủ cần kiểm tra]. *Tạp chí Khoa học & Đào tạo Ngân hàng*, số 221, 10/2020. | VaR cho VN-Index bằng phi tham số, bán tham số, tham số (có CAViaR); phân phối không chuẩn, lệch, đuôi dày cho dự báo tốt nhất. **Bài gần đề nhất.** |
| V2 | *Tạp chí Công Thương*: "Ứng dụng học máy trong ước tính Value at Risk: Phương pháp kết hợp GARCH và LSTM", VN30 2018–2024. | Hướng nghiên cứu tiếp. Cần tác giả, số tạp chí. |
| V3 | *The Contagion Effect from U.S. Stock Market to the Vietnamese and the Philippine Stock Markets: The Evidence of DCC-GARCH Model.* JAFEB, 2021, 8(2), 759–770. | Lây lan Mỹ → VN — MT2, MT5. Cần tác giả. |
| V4 | *International financial integration: Stock return linkages and volatility transmission between Vietnam and advanced countries* (ScienceDirect, ~2017). | VAR, BEKK-GARCH. Cần tác giả, tạp chí. |
| V5 | *The Relationship between the United States and Vietnam Stock Markets* (2003–2009, GARCH-ARMA, EGARCH-ARMA). | Bối cảnh. Cần tác giả. |
| V6 | Nguyễn Anh Phong (2012). *Tạp chí Phát triển Kinh tế*, 264(10), 33–39. | Bối cảnh TTCK VN. |

## 5. Mạch lập luận gợi ý cho phần tổng quan

1. VaR không dưới cộng tính, bỏ qua độ lớn tổn thất trong đuôi (1, 2) → Basel chuyển sang ES 97,5% (23).
2. Lợi suất có đuôi dày và biến động theo cụm (3, 4, 5) → mô hình phi điều kiện dễ đánh giá thiếu rủi ro; mô hình có điều kiện + đuôi dày/EVT làm tốt hơn (10, 18); ở VN, V1 và LA1 cho kết quả tương tự.
3. Đánh giá mô hình cần backtest (6, 7, 16, 22), cho cả ES (10, 20) và theo hàm tổn thất (19, 21, 25).
4. Với nhà đầu tư VN, đa dạng hóa sang Mỹ phụ thuộc tương quan, mà tương quan có xu hướng tăng khi khủng hoảng (14, 15, V3, V4) → đo lợi ích đa dạng hóa theo thời gian và stress test.
5. Khoảng trống → câu hỏi nghiên cứu. Application dựa trên (11, 12).
