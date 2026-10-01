# Hệ thiết kế giao diện — "Bàn điều khiển quản trị rủi ro thị trường"

Giao diện Streamlit (`dashboard/`) được thiết kế theo phong cách **hệ thống quản trị rủi ro của ngân hàng**:
nền sáng, thanh điều hướng navy đậm, điểm nhấn vàng đồng (lấy từ slide đề án), chữ rõ ràng và mọi trạng thái
đều có **biểu tượng + chữ** (không chỉ dựa vào màu). Toàn bộ token và component nằm ở `dashboard/ui.py`;
theme gốc của Streamlit (màu, font, bảng màu biểu đồ) nằm ở `.streamlit/config.toml`.

## 1. Token

### Màu

| Nhóm | Token | Mã | Dùng cho |
|---|---|---|---|
| Thương hiệu | `navy900` | `#0F1E3A` | Nền thanh bên |
| | `navy800` | `#1B2B4B` | Khối "Mục tiêu đề án", vòng tròn tiêu đề, icon |
| | `navy700` | `#1B3A6B` | Màu chính (nút, liên kết, primaryColor) |
| | `gold600` | `#8C6A14` | Dòng chữ nhỏ viết hoa trên tiêu đề (tương phản 5,0:1 trên nền trắng) |
| | `gold500` / `gold300` | `#B8902F` / `#D9B35A` | Nền biểu tượng, viền KPI/khối kết luận, mục đang chọn ở thanh bên (không dùng cho chữ trên nền sáng) |
| Bề mặt | `bg` / `surface` / `border` | `#F4F6FA` / `#FFFFFF` / `#E3E8F0` | Nền trang / thẻ / viền |
| Chữ | `text` / `text2` / `muted` | `#14213D` / `#4A5873` / `#627089` | Chữ chính / phụ / chú thích |
| Trạng thái | `good` / `warn` / `bad` / `info` | `#1A7F37` / `#9A6700` / `#B42318` / `#1B3A6B` | Huy hiệu Đạt / Cảnh báo / Không đạt / Thông tin (kèm nền nhạt `*_bg`) |

Màu trạng thái **chỉ** dùng cho trạng thái, không dùng làm màu chuỗi dữ liệu.

### Bảng màu biểu đồ (theo quy trình của skill *dataviz*)

- **Phân loại** (thứ tự cố định, không xoay vòng): `#2D66AD` xanh navy · `#B07D18` vàng đồng · `#1B9A84` xanh ngọc ·
  `#D0593C` đỏ gạch · `#7C5CB0` tím · `#D9669C` hồng.
  Kiểm định bằng `validate_palette.js --mode light` trên nền `#FFFFFF`: **ALL CHECKS PASS** (dải sáng, độ bão hòa,
  tách biệt cặp kề nhau cho 3 dạng mù màu, ngưỡng thị giác thường, tương phản). Ba màu đầu đạt cả chế độ `--pairs all`,
  nên 3 danh mục chính (100% VN · 50/50 · 100% S&P) luôn dùng ba màu này (`PORT_COLOR`) — màu đi theo danh mục,
  không đổi khi lọc.
- **Tuần tự** (độ lớn, heatmap p-value): một sắc navy từ `#EEF3FA` đến `#122848`.
- **Phân kỳ** (âm/dương): đỏ gạch ↔ xám trung tính `#E9ECF1` ↔ navy.
- Tối đa 6 chuỗi trên một biểu đồ; bộ chọn mô hình giới hạn 3 mô hình để giữ biểu đồ đọc được.

### Chữ

| Vai trò | Font | Ghi chú |
|---|---|---|
| Tiêu đề, số KPI | **Montserrat** (variable 100–900) | Hỗ trợ đầy đủ dấu tiếng Việt |
| Nội dung, bảng | **Be Vietnam Pro** 400/500/600/700 | Thiết kế riêng cho tiếng Việt |

Font được **đóng gói sẵn** trong `dashboard/static/fonts/` (giấy phép SIL OFL kèm theo) và nạp qua
`[[theme.fontFaces]]`, nên máy chấm **không cần Internet** vẫn hiển thị đúng font.
Số hiển thị theo kiểu Việt Nam (`ui.num`): `32,7%`, `4.610 phiên`.

### Khoảng cách, bo góc

Bo góc 12–14 px (thẻ), 8 px (nút), 999 px (huy hiệu); lưới KPI chia đều theo số thẻ (tối đa 4/hàng; 2 cột dưới 900 px, 1 cột trên điện thoại); nội dung tối đa 1320 px.

## 2. Component (`dashboard/ui.py`)

| Hàm | Mục đích | Ghi chú dùng |
|---|---|---|
| `page_header(title, subtitle, eyebrow, ic)` | Tiêu đề trang: vòng tròn navy + dòng chữ nhỏ vàng đồng + tiêu đề Montserrat | Mỗi trang gọi đúng một lần ở đầu |
| `section(title, ic, sub)` | Tiêu đề mục có biểu tượng | |
| `kpis(items)` | Hàng thẻ số liệu chính; mỗi thẻ có nhãn, giá trị, ghi chú, màu viền và huy hiệu tùy chọn | Tối đa 4 thẻ/hàng |
| `pill(kind, text)` / `verdict_pill(ok)` | Huy hiệu trạng thái `good`/`warn`/`bad`/`info` — luôn có ký hiệu ✓ ! ✕ i kèm chữ | Không dùng màu đơn thuần |
| `check_card(title, items)` | Thẻ danh sách "đã đáp ứng" | Trang chủ |
| `navy_panel(title, items)` | Khối nền navy đánh số 1-2-3 | Ba mục tiêu đề án |
| `callout(text_md, heading)` | Khối kết luận có viền vàng | Mỗi trang MT |
| `source_bar()` | Dải nguồn dữ liệu (hai file clean, đối chiếu FRED) và tài liệu nền | Chân trang chủ |
| `table(df, pct, p, num, rename)` | Bảng: tên cột tiếng Việt, % 2 chữ số, p-value 3 chữ số, ẩn chỉ số dòng | Thay cho `st.dataframe` thô |
| `style(fig, height, pct, title)` | Áp template Plotly `nganhang`: font, lưới mờ, chú giải nằm dưới biểu đồ | Mọi biểu đồ Plotly |
| `icon(name, size, color)` | Icon nét mảnh dạng ảnh data-URI | `st.html` lọc thẻ `<svg>` nên phải nhúng qua `<img>` |
| `logo()` | Logo khiên + chữ ở đầu thanh bên (`st.logo`) | |

## 3. Mẫu trang

1. `page_header` → 2. `kpis` (3–4 số quan trọng nhất) → 3. `callout` kết luận → 4. bộ lọc **một hàng** phía trên biểu đồ →
5. biểu đồ (có chú giải + tooltip của Plotly, cho phép phóng to) → 6. bảng số liệu gốc trong tab/expander để đọc chính xác.

Điều hướng chia 4 nhóm: **Tổng quan** (bảng điều khiển, đối chiếu yêu cầu đề) · **Vận hành** (chạy phân tích, kiểm tra tái lập)
· **Kết quả nghiên cứu** (dữ liệu, MT1–MT5, khuyến nghị) · **Tài liệu** (hình, báo cáo & tải về, thuật ngữ).

## 4. Khả năng tiếp cận

- Tương phản chữ/nền ≥ 4,5:1 (WCAG AA) cho mọi màu chữ: `text` 14,8:1 · `text2` 7,2:1 · `muted` 5,0:1 · `gold600` 5,0:1 trên nền trắng;
  chữ sáng `#E6EBF3` trên thanh bên `#0F1E3A` 13,8:1; chữ trạng thái trên nền nhạt tương ứng ≥ 4,5:1.
- Trạng thái luôn là biểu tượng + chữ; biểu đồ ≥ 2 chuỗi luôn có chú giải; số liệu luôn có bảng đi kèm.
- Nút thao tác chính (Chạy toàn bộ, Kiểm tra tái lập) có mô tả thời gian chạy và khóa chống bấm hai lần (`outputs/logs/dang_chay.lock`).

## 5. Việc nên tránh

| Nên | Không nên |
|---|---|
| Dùng `ui.table`, `ui.kpis`, `ui.pill` | Tự viết HTML/CSS trong từng trang |
| Giữ màu danh mục theo `PORT_COLOR` | Đổi màu khi người dùng lọc bớt chuỗi |
| Một trục tung cho mỗi biểu đồ | Biểu đồ hai trục tung |
| Chữ dùng màu chữ, dấu hiệu màu nằm cạnh | Tô chữ bằng màu chuỗi dữ liệu |
