# Application — Phân bổ theo giới hạn ES (bản nháp tự sinh)

> **CẢNH BÁO:** Không có phương pháp nào đồng thời được cả Kupiec và Christoffersen ủng hộ ở VaR 99%. Mô phỏng lịch sử (HS) chỉ được dùng để mô tả kết quả thăm dò, không làm căn cứ kết luận.
> Số liệu: `outputs/tables/T14_allocation_es_limits.csv`, `T14b_allocation_consistency.csv`, `T15_model_recommendation.csv`.

**(a) Kết quả thăm dò — chưa đủ điều kiện kết luận.**
Theo Mô phỏng lịch sử (HS) (ES 97,5% trung bình, %/ngày): Tỷ trọng có ES thấp nhất theo giai đoạn — Bình thường: 50/50 (2.50%); COVID_2020: 100/0 (3.81%); GFC_2008: 50/50 (3.53%); Tightening_2022: 25/75 (2.61%); Toàn kỳ: 50/50 (2.59%); TradeWar_2018: 25/75 (2.35%); VN_2011_2012: 50/50 (2.46%). Ở 6/7 giai đoạn, ít nhất một tỷ trọng kết hợp có ES thấp hơn CẢ HAI danh mục thuần (nhất quán với tính dưới cộng tính của ES).
Kết quả thăm dò **nghiêng về phía Mỹ (tăng tỷ trọng S&P 500) so với danh mục thuần VN-Index**, nhưng không đủ điều kiện để đưa ra kết luận. Ngoại lệ — các giai đoạn mà tỷ trọng có ES thấp nhất nghiêng về VN: COVID_2020; tức là lợi ích của việc thêm S&P phụ thuộc vào việc cú sốc bắt nguồn từ thị trường nào.

**(b) Backtest có ủng hộ kết luận không.** CẢNH BÁO: không phương pháp nào đồng thời vượt qua Kupiec và Christoffersen ở VaR 99% trong các danh mục chính. Các phương pháp xếp hạng đầu theo hai kiểm định VaR và mức thiếu dự báo khi stress (T15): Mô phỏng lịch sử (HS), GARCH(1,1) (GARCH_N), Monte Carlo (MC_Normal).

**(c) Điều kiện làm kết luận thay đổi.** Lợi ích đa dạng hóa **đi kèm với** mức tương quan VN–Mỹ: khi tương quan tăng,
lợi ích thu hẹp (MT2, T8). Với giới hạn minh họa ES 4%/ngày: tỷ trọng thỏa giới hạn lúc bình thường (≤ 5% số ngày vượt): không có;
vẫn thỏa trong mọi giai đoạn stress lõi có dữ liệu: không có tỷ trọng nào (T14b). Về tỷ giá: ΔES do tỷ giá dao động -0.01 đến 0.03 điểm %/ngày (T9). Về lạm phát: ES 100% VN trung bình 3.41% khi lạm phát > 4% so với 2.55% khi lạm phát thấp (p = 0.000, T10) —
so sánh theo bối cảnh, không nhân quả.

**(d) Hạn chế.** Chỉ số không phải tài sản đầu tư trực tiếp (cần ETF/quỹ, có sai lệch theo dõi); bỏ qua phí, thuế và
hạn chế chuyển vốn ra nước ngoài của nhà đầu tư cá nhân Việt Nam; chuỗi tỷ giá có 3 điểm lỗi báo giá đã được lọc
(T0_fx_cleaning_log); kết quả dựa trên dữ liệu quá khứ 02/2006–02/2025 và không đảm bảo cho tương lai.

*Không nêu tỷ trọng % khuyến nghị — chỉ nêu định hướng (CLAUDE.md §2).*
