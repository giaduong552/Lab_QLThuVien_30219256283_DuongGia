# Kịch bản thực hành công cụ AI

Các prompt dưới đây được chuẩn bị để sinh viên chạy thực tế. Chưa có bằng chứng cho thấy chúng đã được chạy trên Google AI Studio hoặc Antigravity IDE trong phiên tạo bộ mã nguồn. Không ghi kết quả gợi ý thành kết quả cá nhân khi chưa thực hiện.

## Prompt 1 - Phân tích

> Bạn là chuyên viên phân tích hệ thống. Thiết kế ứng dụng quản lý thư viện cục bộ cho một thủ thư. Phân biệt đầu sách và bản sao vật lý. Đề xuất danh sách chức năng, tác nhân, luồng mượn/trả/gia hạn và bảng dữ liệu. Giả định: tối đa 3 bản sao đang mượn/độc giả, mượn 14 ngày, gia hạn một lần thêm 7 ngày. Thẻ hết hạn/khóa hoặc còn sách quá hạn không được mượn/gia hạn. Chưa tính tiền phạt. Hãy chỉ ra những giả định cần xác nhận và không tự khẳng định đây là quy định của trường.

## Prompt 2 - Rà soát thiết kế và mã nguồn

> Tôi có ứng dụng Python chuẩn + SQLite + HTML/CSS/JavaScript. Đọc schema.sql, core.py và app.py tôi cung cấp. Kiểm tra khóa ngoại, chỉ mục chống mượn trùng, giao dịch khi mượn/trả, kiểm tra hạn thẻ, giới hạn mượn và tính ngày quá hạn. Chỉ ra lỗi cụ thể kèm vị trí và cách sửa. Không khẳng định đã chạy mã nếu chưa chạy. Nếu cần thêm file, hãy hỏi đúng tên file.

## Prompt 3 - Thiết kế kiểm thử

> Từ quy tắc thư viện đã nêu, lập bảng kiểm thử gồm ID, tiền điều kiện, đầu vào, bước chạy và kết quả mong đợi. Bao gồm đúng ngày hết hạn thẻ, đúng ngày hạn trả, mượn cuốn thứ tư, hai yêu cầu mượn cùng một bản sao, trả hai lần, trả hư hỏng/thất lạc và dữ liệu trùng mã. Phân biệt kết quả mong đợi với kết quả thực tế. Để trống kết quả thực tế nếu chưa chạy.

## Cách thu thập minh chứng

1. Truy cập https://aistudio.google.com/ và đăng nhập bằng tài khoản cá nhân; tự xử lý bước đăng nhập nếu được yêu cầu.
2. Chạy prompt phân tích. Chụp phần prompt và phản hồi có liên quan, không để lộ email, API key hoặc thông tin nhạy cảm.
3. Mở thư mục dự án trong Antigravity IDE trên máy; chụp cây thư mục và tệp mã nguồn.
4. Chạy lệnh khởi động trong terminal, mở trang ứng dụng và thực hiện kịch bản mượn/trả.
5. Lưu ảnh theo hướng dẫn trong `minh_chung/README.md`; ghi nhận điều chỉnh thực tế bên dưới.

## Nhật ký cá nhân cần bổ sung

| Thời điểm | Công cụ thực dùng | Prompt/thao tác | Phát hiện thực tế | Điều chỉnh đã thực hiện | Tệp ảnh |
|---|---|---|---|---|---|
| [Điền sau khi chạy] | | | | | |

Sinh viên đọc và giải thích được các quy tắc trong `core.py`, thay vì chỉ sao chép kết quả AI.
