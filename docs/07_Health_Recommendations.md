# 7. Phê duyệt & Đẩy khuyến nghị sức khỏe

## 1. Mục đích
Tạo kênh giao tiếp thông tin chính thống một chiều từ Sở Tài nguyên Môi trường đến người dân. Phát đi các chỉ đạo, hướng dẫn hành động (như yêu cầu các cơ sở ngừng đốt lò, yêu cầu người dân đeo khẩu trang) thay vì chỉ thông báo mức độ ô nhiễm khô khan.

## 2. Cách hoạt động
- Quản lý vào tab "Khuyến nghị", điền form thông tin:
  - Chọn "Làng nghề áp dụng" (hoặc chọn Gửi toàn tỉnh).
  - Soạn nội dung (ví dụ: Khuyến cáo hạn chế ra đường từ 17h-19h).
- Bấm Gửi.
- Hệ thống lưu nội dung này vào DB dưới dạng Entity `Recommendation`.
- Giao diện người dân lập tức hiển thị nội dung này trong mục Bảng tin/Khuyến nghị.

## 3. Kỹ thuật & Công nghệ sử dụng
- **RESTful API Design:** Xây dựng CRUD endpoints tiêu chuẩn cho `Recommendation` resource (Tạo, Sửa, Đọc, Xóa).
- **Role-Based Access Control (RBAC):** Cả Backend và Frontend đều kiểm tra phân quyền (Role = `MANAGER`) thông qua JWT Token mới cho phép truy cập form tạo khuyến nghị.
- **Form Handling:** Sử dụng các thẻ form cơ bản kết hợp state React (`useState`) để kiểm soát các input, validate dữ liệu trống trước khi gửi API.

## 4. Tệp mã nguồn tham khảo
- Frontend: `frontend/src/pages/Recommendations.jsx`
- Backend: `backend/app/api/routes/alert.py` (Chứa endpoint POST recommendation)
