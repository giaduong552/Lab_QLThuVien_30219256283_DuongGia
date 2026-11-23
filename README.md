# Library Lab - Quản lý thư viện

**Sinh viên:** Dương Gia - **MSSV:** 30219256283  
**Thư mục dự án:** `Lab_QLThuVien_30219256283_DuongGia`

Ứng dụng web cục bộ: HTML/CSS/JavaScript thuần, Python và SQLite. Không cần npm, pip, tài khoản đám mây hoặc API key. AI được dùng hỗ trợ phát triển; ứng dụng không có chatbot AI.

## 1. Yêu cầu và khởi chạy

- Python 3.10 trở lên, có module SQLite tiêu chuẩn.
- Trình duyệt hiện đại như Edge/Chrome.
- Giải nén ZIP trước khi chạy. Mở terminal tại thư mục dự án chứa README này.

```powershell
python --version
python src/app.py
```

Mở **http://127.0.0.1:8000**. Giữ terminal đang chạy, nhấn Ctrl+C để dừng. Trên Windows có thể nhấp đúp `START_WINDOWS.bat` (nếu `python` đã được thêm vào PATH).

Nếu Windows chỉ nhận lệnh `py`, thay `python` bằng `py` trong các lệnh. Nếu cổng 8000 đã được dùng:

```powershell
python src/app.py --port 8001
```

Sau đó mở http://127.0.0.1:8001. Không mở trực tiếp `index.html`, vì giao diện cần API Python.

## 2. Dữ liệu mẫu và cách dùng

Lần chạy đầu, ứng dụng tạo `src/data/library.db` với 8 đầu sách, 24 bản sao, 4 độc giả, 3 phiếu. Tên tác giả, sách, nhà xuất bản và độc giả là dữ liệu giả lập; mã `DEMO-*` là mã danh mục, không phải ISBN đã xác thực.

1. **Tổng quan:** xem số đầu sách, bản sao sẵn sàng, phiếu đang mượn và quá hạn.
2. **Danh mục sách:** thêm/sửa/xóa đầu sách; tra cứu không dấu theo tên, tác giả, mã hoặc thể loại.
3. **Kho bản sao:** tạo từng cuốn vật lý thuộc đầu sách; đặt mã duy nhất, vị trí kệ; theo dõi sẵn sàng/đang mượn/hỏng/mất.
4. **Độc giả:** quản lý thẻ, hạn thẻ, khóa thẻ, xem lịch sử từng người.
5. **Mượn & trả:** chọn độc giả và bản sao, lập phiếu, gia hạn hoặc trả với tình trạng thực tế.
6. **Thống kê:** tình trạng kho, 5 đầu sách có nhiều lượt mượn, phiếu cần thu hồi. Các trang danh sách có xuất CSV tiếng Việt, theo bộ lọc hiện tại; thống kê xuất toàn bộ lịch sử mượn.

**Kịch bản nhanh:** dùng DG004 mượn S001-02; xác nhận trạng thái đang mượn; gia hạn một lần; trả nguyên vẹn; kiểm tra bản sao trở lại sẵn sàng. DG001 có phiếu quá hạn để thử tình huống bị từ chối. S008-03 đang hư hỏng.

Quy định giả định của bài: tối đa 3 bản sao/độc giả, mượn 14 ngày, gia hạn tối đa 1 lần thêm 7 ngày từ hạn trả cũ. Thẻ hết hạn/khóa hoặc còn sách quá hạn sẽ không được mượn/gia hạn. Đến đúng ngày hết hạn thẻ vẫn hợp lệ; đúng ngày hạn trả chưa tính quá hạn. Trả sách vẫn được phép khi thẻ khóa/hết hạn. Không tính tiền phạt/bồi thường.

## 3. Kiểm thử

```powershell
python -m unittest discover -s tests -v
```

26 phương thức kiểm thử trên SQLite tạm: nghiệp vụ, ranh giới ngày, dữ liệu sai, bảo vệ lịch sử, cạnh tranh mượn và bộ xử lý HTTP. Bốn kiểm thử HTTP dùng luồng byte trong bộ nhớ, không mở kết nối TCP. Log thực tế nằm ở `minh_chung/test_results.txt`. Không coi kết quả này là kiểm thử E2E trình duyệt.

Nếu đã cài Node.js, có thể kiểm tra cú pháp JavaScript (Node không cần thiết để chạy app):

```powershell
node --check src/static/app.js
```

Các bước kiểm tra trình duyệt cần thực hiện và ghi kết quả nằm trong báo cáo. Việc kiểm tra giao diện bằng trình duyệt trong phiên tạo bài chưa hoàn tất do giới hạn môi trường.

## 4. Sao lưu, khôi phục và tạo lại mẫu

- Dừng ứng dụng trước khi sao lưu. Sao chép `src/data/library.db` đến nơi an toàn.
- Khôi phục: dừng app, thay DB hiện tại bằng bản sao lưu rồi khởi động lại.
- Thử dữ liệu mẫu mới mà không đụng DB cũ: `python src/app.py --db src/data/demo_moi.db --port 8001`. Đặt một tên DB chưa tồn tại. Mẫu chỉ sinh một lần cho mỗi DB.
- CSV phục vụ báo cáo; ứng dụng chưa có chức năng nhập CSV/khôi phục từ CSV.

## 5. Cấu trúc dự án

| Đường dẫn | Vai trò |
|---|---|
| `src/app.py` | Máy chủ cục bộ, định tuyến API, kiểm tra request |
| `src/core.py` | Quy tắc mượn/trả, CRUD, dữ liệu mẫu, giao dịch |
| `src/schema.sql` | Bảng, khóa ngoại, ràng buộc và chỉ mục |
| `src/static/` | Giao diện HTML, CSS, JavaScript |
| `tests/test_library.py` | 26 kiểm thử tự động |
| `BaoCao_Lab.md` | Báo cáo phân tích, sơ đồ Mermaid, thiết kế, kiểm thử |
| `PROMPTS_AI.md` | Prompt để thực hành Google AI Studio / IDE và ghi bằng chứng |
| `minh_chung/` | Log kiểm thử và hướng dẫn bổ sung ảnh thật |

## 6. Đưa lên GitHub

**Chưa đẩy lên GitHub trong phiên tạo bài:** chưa có repository đích và kết nối GitHub xác thực. Các lệnh dưới đây là hướng dẫn, không phải bằng chứng đã thực hiện.

Tạo repository trống tên `Lab_QLThuVien_30219256283_DuongGia` trên tài khoản GitHub của bạn. Chạy tại thư mục dự án:

```powershell
git init
git add .
git commit -m "Build library management lab"
git branch -M main
git remote add origin https://github.com/TEN_TAI_KHOAN/Lab_QLThuVien_30219256283_DuongGia.git
git push -u origin main
```

Thay `TEN_TAI_KHOAN` bằng tài khoản thật; đăng nhập GitHub khi Git yêu cầu. Nếu Git yêu cầu danh tính commit, cấu hình tên/email của bạn trong repository trước. `.gitignore` loại DB đang sử dụng, môi trường ảo và cache khỏi commit; source tự sinh dữ liệu mẫu khi chạy.

Sau khi push thành công, điền URL và commit vào mục 9 báo cáo, thêm ảnh minh chứng, cập nhật lại ZIP. Có thể tải ZIP từ nút Code của GitHub rồi đổi tên, hoặc dùng Compress-Archive như dưới đây (đảm bảo chưa có file cùng tên):

```powershell
Compress-Archive -Path Lab_QLThuVien_30219256283_DuongGia -DestinationPath 30219256283_DuongGia_LabQLThuVien.zip
```

Lệnh đóng gói được chạy từ thư mục cha của dự án.

## 7. Giới hạn

Đây là ứng dụng thực hành một vai trò thủ thư, chưa có đăng nhập/phân quyền, nhật ký người thao tác, phân trang hoặc nhiều chi nhánh. Máy chủ chỉ bind `127.0.0.1`; không triển khai công khai bằng máy chủ demo này. Không dùng dữ liệu cá nhân thật khi trình diễn bài học.
