# Câu trả lời tự sinh cho các mục tiêu nghiên cứu

## Kiem_dinh_gia_dinh

- Jarque–Bera bác bỏ phân phối chuẩn ở 5/5 chuỗi → giả định chuẩn của Normal và MC_Normal không được dữ liệu ủng hộ; HS (không giả định phân phối) là mô hình đối chứng.
- ARCH-LM(10) có ý nghĩa ở 4/5 chuỗi và Ljung–Box trên r² ở 4/5 chuỗi → biến động theo cụm, là căn cứ dùng GARCH(1,1).
- ADF bác bỏ nghiệm đơn vị ở 5/5 chuỗi lợi suất (KPSS không bác bỏ tính dừng ở 5/5) → mô hình hóa trên lợi suất là phù hợp.

## MT1

- ES 97,5% trung bình (mẫu chung) của danh mục 50/50 thấp hơn 100% VN ở 4/4 phương pháp; mức giảm trung vị 32.7% (từ 30.6% đến 34.1%) — T4_var_es_overall.
- ES trung bình 100% VN: 3.16%/ngày; 50/50: 2.13%; 100% S&P (VND): 2.70% (trung vị qua các mô hình).
- Chênh lệch giữa mô hình cao nhất và thấp nhất: VN 0.75 điểm %, 50/50 0.63, S&P 0.87 → lựa chọn mô hình quan trọng không kém lựa chọn tỷ trọng.

## MT2

- Lợi ích đa dạng hóa tương đối (DR) trung bình 29.6% khi tương quan 252 phiên ở tam phân vị thấp, so với 24.3% ở tam phân vị cao (chênh -5.3 điểm %, p block bootstrap = 0.015) — T8_diversification_by_corr.
- Hồi quy mô tả DR theo ρ (Newey–West): b = -0.115 (p = 0.133); hệ số âm nghĩa là lợi ích đa dạng hóa **đi kèm với** mức thấp hơn khi tương quan cao hơn (không hàm ý nhân quả).
- Tương quan khi cả hai thị trường cùng giảm mạnh (10% đuôi) = 0.13 so với 0.05 nếu lợi suất là Normal cùng ρ — T8b_tail_correlation.
- Với dữ liệu lệch pha, tương quan trong các giai đoạn stress dao động 0.12–0.37 (yên ổn 0.19); sau hiệu chỉnh Forbes–Rigobon còn 0.06–0.26 — T8d_forbes_rigobon.

## MT3

- Toàn kỳ, ΔES_FX của 100% S&P = -0.01 đến 0.03 điểm %/ngày tùy mô hình; tương quan r_S&P(USD) với r_USD/VND = -0.003 — T9_fx_effect.
- Component ES (50/50, toàn kỳ): VN 54.5%, S&P (USD) 46.0%, tỷ giá -0.4% tổng ES — T9b_component_es.
- Lạm phát cao (> 4%) trùng với ES 100% VN trung bình 3.41% so với 2.55% khi lạm phát thấp (p = 0.000); DR trung bình 26.7% vs 25.7% — T10_inflation_regimes.
- Đây là so sánh theo bối cảnh: các tháng lạm phát cao trùng với những cú sốc khác (2008, 2011, 2022) nên không tách được tác động riêng của lạm phát.

## VAR_lan_toa

- VAR(1) chọn theo BIC, mô hình ổn định = True. S&P 500 → VN-Index: F = 278.4, p = 6.7e-62; USD/VND → VN-Index: p = 0.873 — T16_var_granger.
- Sau 10 ngày, cú sốc S&P giải thích 6.7% và tỷ giá 0.1% phương sai sai số dự báo của VN-Index — T16_var_fevd.

## MT5

- Trung bình qua 4 giai đoạn lõi và 3 danh mục, tỷ lệ vi phạm VaR99 gấp 9.0 lần kỳ vọng với Normal (cao nhất) và 5.5 lần với GARCH_N (thấp nhất) — T11_stress_historical.
- Mô hình xuất hiện nhiều nhất ở vị trí 'đánh giá thiếu rủi ro nhất': Normal (8), GARCH_N (4), MC_Normal (2) — T11b_stress_worst_models.
- Số phiên trung vị từ vi phạm VaR99 đầu tiên trong giai đoạn đến khi VaR99 tăng gấp đôi: mô hình có điều kiện 10 phiên, mô hình phi điều kiện 16 phiên (cột reaction_lag_days; bỏ qua trường hợp VaR không tăng gấp đôi trong 60 phiên).
