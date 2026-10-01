# Tổng quan tài liệu (bản dùng cho báo cáo)

> Danh mục đầy đủ và mức độ chắc chắn: `docs/TONG_QUAN_TAI_LIEU.md`. Tài liệu đánh dấu [CITE] phải được nhóm mở và kiểm tra trước khi nộp.
> Rubric yêu cầu ≥ 5 bài có bài nền tảng: đề án dùng 3 bài nền tảng đề yêu cầu (Bollerslev 1986; Kupiec 1995; Christoffersen 1998) và hơn 20 bài khác.

## 1. Thước đo rủi ro: từ VaR đến ES
VaR là phân vị của phân phối lỗ và trở thành chuẩn ngành từ thập niên 1990 (Jorion, 2006). Artzner et al. (1999) chỉ ra VaR
không thỏa tính dưới cộng tính — rủi ro của danh mục có thể lớn hơn tổng rủi ro thành phần — và không phản ánh độ lớn tổn thất
vượt ngưỡng. Acerbi & Tasche (2002) chứng minh ES là thước đo nhất quán. Basel Committee (2019) trong FRTB chuyển chỉ tiêu vốn
rủi ro thị trường sang ES 97,5%. → Đề án dùng ES 97,5% làm chỉ tiêu chính, VaR 95/99% bổ sung.

## 2. Mô hình biến động có điều kiện
Engle (1982) đưa ra ARCH; Bollerslev (1986) mở rộng thành GARCH(1,1) — mô hình đề yêu cầu. Các kiểm định ARCH-LM, sign-bias,
GJR và EWMA là các hướng nghiên cứu liên quan được nêu trong tài liệu nền, không được triển khai trong phạm vi công cụ hiện tại.

## 3. So sánh phương pháp dự báo VaR
Kuester et al. (2006) so sánh nhiều chiến lược trên dữ liệu thực và thấy mô hình có điều kiện kết hợp phân phối đuôi dày hoặc EVT
vượt trội mô hình phi điều kiện. McNeil & Frey (2000) đề xuất GARCH-EVT: lọc GARCH rồi mô hình hóa đuôi phần dư bằng GPD, kèm
kiểm định phần dư vượt cho ES. Các lựa chọn khác: HS trọng số tuổi (Boudoukh et al., 1998), FHS (Barone-Adesi et al., 1999),
CAViaR mô hình hóa trực tiếp phân vị (Engle & Manganelli, 2004). Đây là bối cảnh tổng quan tài liệu; pipeline hiện hành chỉ
triển khai bốn phương pháp theo phạm vi đề án: HS, Normal, MC_Normal và GARCH_N.

## 4. Kiểm định ngược
Kupiec (1995) kiểm định tỷ lệ vi phạm (POF); Christoffersen (1998) kiểm tra tính độc lập và bao phủ có điều kiện. Công cụ hiện
tại chỉ triển khai hai kiểm định này cho VaR. Các phương pháp duration, Basel traffic-light, backtest ES và so sánh/xếp hạng
thống kê giữa mô hình được nhắc đến như tài liệu nền nhưng không nằm trong implementation.

## 5. Liên kết thị trường Việt Nam – Mỹ và tương quan khủng hoảng
Longin & Solnik (2001) cho thấy tương quan quốc tế tăng khi thị trường cùng giảm; Forbes & Rigobon (2002) cảnh báo tương quan
có điều kiện theo giai đoạn biến động cao bị chệch lên. Engle (2002) đề xuất DCC. Với Việt Nam: bằng chứng lây lan từ Mỹ trong
khủng hoảng dưới vay và COVID-19 bằng DCC-GARCH (V3), liên kết và lan tỏa biến động bằng VAR/BEKK-GARCH (V4), S&P 500 tác động
đến lợi suất VN-Index giai đoạn 2003–2009 (V5) [CITE — cần tên tác giả cho V3–V5]. Mô hình VAR và nhân quả Granger theo Sims (1980),
Granger (1969) và Bài 9 của môn học.

## 6. Nghiên cứu VaR tại Việt Nam
Lê Hải Trung & Nguyễn Thị Mai Trang (2020) so sánh phương pháp phi tham số, bán tham số và tham số (có CAViaR) cho VN-Index; giả
định phân phối lệch và đuôi dày cho dự báo chính xác nhất. Luận án của Hoàng Đức Mạnh (ĐH Kinh tế Quốc dân) về các mô hình đo lường
rủi ro trên TTCK Việt Nam [CITE — cần kiểm tra năm]. Hướng học máy GARCH–LSTM cho VN30 (V2). Bối cảnh thanh khoản TTCK Việt Nam:
Nguyễn Anh Phong (2012).

## 7. Khoảng trống và đóng góp
Nghiên cứu trong nước tập trung vào rủi ro của riêng VN-Index/VN30. Đề án đo **ES danh mục Việt–Mỹ quy đổi VND**, backtest VaR
bằng Kupiec và Christoffersen, stress test nhiều giai đoạn và **lợi ích đa dạng hóa theo thời gian**. Pipeline chỉ triển khai HS,
Normal, MC_Normal và GARCH_N; các phương pháp khác trong tổng quan không phải mô hình chạy trong công cụ.
