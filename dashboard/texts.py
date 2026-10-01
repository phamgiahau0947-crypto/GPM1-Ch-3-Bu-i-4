"""Văn bản giải thích dùng trong giao diện (do nhóm soạn — chuyển nguyên từ dashboard cũ của nhóm)."""

PORTFOLIO_INFO = {
    "VN100": {
        "name": "100 % VN-Index",
        "desc": (
            "Danh mục đầu tư **100 % vào thị trường Việt Nam** (VN-Index). "
            "Đây là danh mục tập trung hoàn toàn vào rủi ro nội địa — không có "
            "yếu tố đa dạng hóa quốc tế, do đó biến động phụ thuộc hoàn toàn "
            "vào tình hình kinh tế–tài chính Việt Nam."
        ),
    },
    "VN50_SP50": {
        "name": "50 % VN / 50 % S&P (VND)",
        "desc": (
            "Danh mục **50/50** giữa VN-Index và S&P 500 (quy đổi VND). "
            "Kết hợp lợi suất hai thị trường, có tính đa dạng hóa quốc tế. "
            "Rủi ro tỷ giá USD/VND được phản ánh trong phần S&P 500 đã quy VND."
        ),
    },
    "SP100": {
        "name": "100 % S&P 500 (VND)",
        "desc": (
            "Danh mục **100 % S&P 500** tính bằng VND. Phản ánh rủi ro thị trường Mỹ "
            "cộng thêm rủi ro tỷ giá USD/VND cho nhà đầu tư Việt Nam."
        ),
    },
}

MODEL_INFO = {
    "HS": (
        "**Mô phỏng lịch sử (Historical Simulation / HS):** Sử dụng phân phối "
        "thực nghiệm của lợi suất quá khứ (cửa sổ 252 ngày) để ước lượng "
        "phân vị. Đơn giản, không giả định phân phối, nhưng phản ứng chậm "
        "với thay đổi biến động."
    ),
    "Normal": (
        "**Phương pháp tham số (Normal):** Giả định lợi suất tuân theo phân phối chuẩn. "
        "VaR = μ − z_α × σ. Đơn giản nhưng thường **đánh giá thấp rủi ro đuôi** "
        "vì lợi suất tài chính có đuôi dày hơn phân phối chuẩn."
    ),
    "MC_Normal": (
        "**Monte Carlo (MC_Normal):** Mô phỏng 10 000 kịch bản lợi suất ngẫu nhiên "
        "từ phân phối chuẩn với μ, σ ước lượng → lấy phân vị. Linh hoạt "
        "nhưng mang hạn chế của giả định Normal."
    ),
    "GARCH_N": (
        "**GARCH(1,1) (GARCH_N):** Mô hình hóa biến động có điều kiện "
        "(σ²_t = ω + α·ε²_{t-1} + β·σ²_{t-1}) với đổi mới Normal. "
        "Nắm bắt hiệu ứng **volatility clustering** (biến động theo cụm)."
    ),
}

LEVEL_INFO = {
    "VaR_99": {
        "label": "VaR 99 %",
        "desc": (
            "**Value-at-Risk ở mức tin cậy 99 %:** Khoản lỗ tối đa mà danh mục "
            "dự kiến *không vượt quá* trong 99 % số ngày giao dịch. Hay nói cách "
            "khác, chỉ khoảng **1 ngày trong 100** lợi suất thực tế sẽ xấu hơn "
            "mức VaR này."
        ),
        "alpha_expected": "1 %",
    },
    "VaR_975": {
        "label": "VaR 97,5 %",
        "desc": (
            "**Value-at-Risk ở mức tin cậy 97,5 %:** Khoản lỗ tối đa dự kiến "
            "không bị vượt trong 97,5 % số ngày — khoảng **2,5 ngày trong 100**."
        ),
        "alpha_expected": "2,5 %",
    },
    "VaR_95": {
        "label": "VaR 95 %",
        "desc": (
            "**Value-at-Risk ở mức tin cậy 95 %:** Ngưỡng lỗ thấp hơn, bị vượt "
            "khoảng **5 ngày trong 100**. Thường dùng theo khuyến nghị Basel II."
        ),
        "alpha_expected": "5 %",
    },
    "ES_975": {
        "label": "ES 97,5 %",
        "desc": (
            "**Expected Shortfall (CVaR) ở mức 97,5 %:** Kỳ vọng tổn thất "
            "trung bình trong **2,5 % ngày tệ nhất**. ES luôn ≥ VaR cùng mức "
            "và phản ánh rủi ro đuôi tốt hơn VaR — được Basel III khuyến nghị."
        ),
        "alpha_expected": None,
    },
}

PERIOD_INFO = {
    "Toàn kỳ": (
        "📊 **Toàn kỳ:** Hiển thị toàn bộ dữ liệu lịch sử từ 2006 đến nay, "
        "bao gồm nhiều giai đoạn thị trường khác nhau (tăng trưởng, khủng hoảng, "
        "phục hồi). Kết quả backtest trên toàn kỳ phản ánh khả năng tổng quát "
        "của mô hình."
    ),
    "Khủng hoảng tài chính toàn cầu 2008": (
        "📉 **Khủng hoảng tài chính toàn cầu (01/2008 – 03/2009):** "
        "Sự sụp đổ của Lehman Brothers, thị trường toàn cầu giảm trên 50 %. "
        "VN-Index giảm từ ~900 xuống ~240 điểm. Giai đoạn này kiểm tra khả năng "
        "dự báo rủi ro **đuôi cực đoan** của mô hình — nhiều mô hình đơn giản "
        "(Normal, HS) thường **đánh giá thấp** rủi ro."
    ),
    "Lạm phát cao & tái cơ cấu ngân hàng VN 2011–2012": (
        "🏦 **Lạm phát cao & tái cơ cấu VN (01/2011 – 12/2012):** "
        "CPI Việt Nam tăng trên 18 %, lãi suất qua đêm vượt 20 %, "
        "VN-Index giảm mạnh và thanh khoản cạn kiệt. Giai đoạn này "
        "đặc trưng cho **rủi ro nội địa riêng** — danh mục 100 % VN chịu "
        "ảnh hưởng nặng nhất, trong khi 100 % S&P ít bị tác động."
    ),
    "Căng thẳng thương mại Mỹ–Trung 2018": (
        "⚔️ **Căng thẳng thương mại Mỹ–Trung (02/2018 – 12/2018):** "
        "Chiến tranh thuế quan Mỹ–Trung khiến cả hai thị trường đều biến "
        "động mạnh. VN-Index giảm ~27 % từ đỉnh tháng 4. Giai đoạn "
        "cho thấy **rủi ro lan tỏa** giữa hai thị trường — danh mục 50/50 "
        "không nhất thiết an toàn hơn khi tương quan tăng."
    ),
    "COVID-19 2020": (
        "🦠 **COVID-19 (20/02/2020 – 30/04/2020):** Cú sốc bất ngờ, "
        "VN-Index giảm ~33 % từ 22/01 đến 24/03/2020. S&P 500 có ngày giảm kỷ lục "
        "(-12 %). Đặc trưng: biến động cực cao trong thời gian ngắn — "
        "thử thách khả năng phản ứng nhanh của các phương pháp biến động có điều kiện."
    ),
    "Thắt chặt tiền tệ & lạm phát 2022": (
        "📈 **Thắt chặt tiền tệ & lạm phát (01/2022 – 12/2022):** "
        "Fed tăng lãi suất nhanh nhất 40 năm, USD/VND có lúc tăng ~9 % (đỉnh 11/2022; cả năm ~3,8 %), "
        "VN-Index giảm ~33 %. Giai đoạn này kiểm tra khả năng mô hình "
        "trong bối cảnh **rủi ro tỷ giá + rủi ro thị trường kép** — "
        "danh mục có S&P chịu thêm tác động từ biến động USD/VND."
    ),
}


GLOSSARY_MD = (
        "| Thuật ngữ | Ý nghĩa |\n"
        "|---|---|\n"
        "| **VaR** *(Value-at-Risk)* | Ngưỡng lỗ tối đa ở mức tin cậy cho trước. VD: VaR 99 % = lỗ tối đa trong 99 % số ngày |\n"
        "| **ES** *(Expected Shortfall / CVaR)* | Tổn thất kỳ vọng trung bình trong những ngày vượt VaR — luôn ≥ VaR, phản ánh rủi ro đuôi tốt hơn |\n"
        "| **Backtest** *(Kiểm định ngược)* | So sánh dự báo VaR với lợi suất thực tế để đánh giá mô hình |\n"
        "| **Vi phạm** *(Exceedance)* | Ngày mà lỗ thực tế vượt qua VaR dự báo |\n"
        "| **Kupiec (UC)** | Kiểm định Kupiec — tỷ lệ vi phạm có bằng mức danh nghĩa? p < 0,05 → bác bỏ |\n"
        "| **Christoffersen (CC)** | Kiểm định kết hợp — tỷ lệ vi phạm + tính độc lập (vi phạm không theo cụm?) |\n"
        "| **Rolling** | Tính trượt trên cửa sổ N ngày (VD: 252 ngày ≈ 1 năm giao dịch) |\n"
        "| **Volatility clustering** | Hiện tượng biến động theo cụm — ngày biến động lớn thường đi theo ngày biến động lớn |\n"
        "| **Đuôi dày** *(Fat tail)* | Lợi suất tài chính có xác suất xảy ra giá trị cực đoan cao hơn phân phối chuẩn |\n"
        "| **GARCH** | Mô hình biến động có điều kiện — σ² thay đổi theo thời gian |\n"
        "| **Monte Carlo** | Ước lượng VaR/ES từ các kịch bản ngẫu nhiên mô phỏng |\n"
        "| **GARCH(1,1)** | Mô hình biến động có điều kiện: phương sai phụ thuộc cú sốc và phương sai kỳ trước |"
)

MODEL_GUIDE_MD = (
            "Bốn phương pháp trong phạm vi đề bài:\n\n"
            "| Tên trong đề | Tên trong công cụ | Đo lường / Đặc điểm |\n"
            "|---|---|---|---|\n"
            "| Mô phỏng lịch sử | **HS** | Phân vị thực nghiệm từ lợi suất quá khứ; không giả định phân phối |\n"
            "| Phương pháp tham số | **Normal** | VaR/ES từ trung bình, độ lệch chuẩn và phân phối chuẩn |\n"
            "| Monte Carlo | **MC_Normal** | Mô phỏng 10.000 kịch bản từ phân phối chuẩn; seed cố định |\n"
            "| GARCH(1,1) | **GARCH_N** | Phương sai có điều kiện với đổi mới chuẩn; nắm bắt biến động theo cụm |"
)
