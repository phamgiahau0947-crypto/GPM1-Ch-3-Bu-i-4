"""Hướng dẫn sử dụng dashboard cho người mới."""

import streamlit as st

from dashboard import ui


def page() -> None:
    ui.page_header(
        "Hướng dẫn sử dụng",
        "Bắt đầu từ đây nếu bạn mới mở dashboard — các mục MT là các câu hỏi nghiên cứu, không phải nút chạy riêng.",
        ic="book",
    )

    ui.section("Bắt đầu trong 3 bước", "play")
    steps = [
        ("Chạy phân tích", "Mở trang Chạy phân tích. Lần đầu nên bấm “Bắt đầu chạy toàn bộ” để tính dự báo từ hai file clean."),
        ("Chờ tiến trình hoàn tất", "Có thể chuyển sang trang khác trong lúc chạy; quay lại trang Chạy phân tích để xem nhật ký và trạng thái."),
        ("Xem kết quả", "Mở Bảng điều khiển để xem tóm tắt, hoặc chọn MT1–MT5 ở thanh bên để xem từng nội dung."),
    ]
    ui.navy_panel("Luồng sử dụng", steps, ic="play")
    left, right = st.columns(2, gap="large")
    with left:
        ui.section("Chạy toàn bộ hay chạy lại nhanh?", "layers")
        st.markdown(
            "- **Bắt đầu chạy toàn bộ:** tính lại các dự báo rolling; dùng khi lần đầu chạy, dữ liệu/cấu hình đổi "
            "hoặc cần xác minh từ đầu. Đây là lựa chọn lâu nhất.\n"
            "- **Chạy lại nhanh:** dùng lại dự báo đã cache nếu còn hợp lệ và tạo lại bảng/hình. Nếu cache chưa có "
            "hoặc đã cũ, phần dự báo vẫn phải tính lại.\n"
            "- **Chạy kiểm thử:** chỉ kiểm tra công thức/code; không tạo bộ kết quả nghiên cứu.\n\n"
            "Pipeline đọc hai file clean trong data/clean. Các dự báo VaR/ES được tính từ chuỗi lợi suất và cửa sổ lịch sử; "
            "chương trình không chỉ đọc sẵn một bảng kết quả có sẵn."
        )
    with right:
        ui.section("MT1–MT5 là gì?", "target")
        st.markdown(
            "- **MT1 · Rủi ro & mô hình:** VaR/ES của ba danh mục, so sánh bốn phương pháp.\n"
            "- **MT2 · Đa dạng hóa:** lợi ích giảm ES đi kèm với tương quan VN–Mỹ như thế nào.\n"
            "- **MT3 · Tỷ giá & lạm phát:** ảnh hưởng khi quy đổi S&P sang VND và so sánh theo bối cảnh lạm phát.\n"
            "- **MT4 · Backtest:** Kupiec và Christoffersen kiểm tra dự báo VaR; đây không phải kiểm định ES.\n"
            "- **MT5 · Stress test:** xem rủi ro trong giai đoạn 2008, 2018, 2020 và 2022.\n\n"
            "Chạy pipeline một lần sẽ tạo kết quả cho các MT; không cần chạy từng MT riêng."
        )
    ui.section("Chọn mô hình và danh mục", "chart")
    st.markdown(
        "Ở trang **Khuyến nghị**, mục **Thử tỷ trọng tùy ý** cho phép chọn tỷ trọng VN/S&P, cửa sổ lịch sử và mô hình. "
        "Chọn **Tự động — theo backtest** để dùng mô hình đứng đầu bảng khuyến nghị hiện tại; hoặc chọn HS, Normal, "
        "MC_Normal hay GARCH_N để xem riêng từng phương pháp. Khi thay lựa chọn, dự báo của tỷ trọng đó được tính bằng "
        "mô hình đã chọn; lần tính đầu có thể mất thời gian và các lựa chọn đã tính được cache."
    )
    st.info(
        "Lưu ý: lựa chọn tự động là ứng viên theo kết quả xếp hạng/backtest trên dữ liệu hiện tại, không phải bảo đảm "
        "mô hình luôn tốt nhất trong tương lai. Khuyến nghị phân bổ cuối cùng vẫn mang tính định tính."
    )
    ui.section("Đi tới trang thường dùng", "play")
    c1, c2, c3 = st.columns(3)
    c1.page_link(st.session_state["_pages"]["chay"], label="Mở Chạy phân tích", icon="▶️", width="stretch")
    c2.page_link(st.session_state["_pages"]["trang-chu"], label="Mở Bảng điều khiển", icon="📊", width="stretch")
    c3.page_link(st.session_state["_pages"]["application"], label="Mở Khuyến nghị", icon="🎯", width="stretch")
