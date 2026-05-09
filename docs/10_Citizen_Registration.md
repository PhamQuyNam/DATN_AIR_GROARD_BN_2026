# 10. Đăng ký & Trạm quan tâm (Dành cho Người dân)

## 1. Mục đích
Cá nhân hóa trải nghiệm theo dõi thông tin môi trường. Tính năng này giúp người dân không bị "bội thực" bởi dữ liệu toàn tỉnh, mà chỉ tập trung vào khu vực họ sinh sống hoặc làm việc.

## 2. Cách hoạt động
- **Đăng ký tài khoản:** Người dân điền thông tin và tạo account với Role = `CITIZEN`.
- **Thiết lập trạm yêu thích:** Vào tab "Trạm quan tâm", người dân chọn từ danh sách 18 làng nghề các khu vực muốn theo dõi. Click nút trái tim để thêm/xóa.
- **Trải nghiệm cá nhân hóa:** Ở trang chủ (Overview), hệ thống sẽ chỉ render ra các Widget bản báo cáo AQI của những làng nghề đã chọn. Cảnh báo khẩn cấp cũng sẽ ưu tiên hiển thị liên quan đến các trạm này.

## 3. Kỹ thuật & Công nghệ sử dụng
- **JWT (JSON Web Token) Auth:** 
  - Đảm bảo an toàn bảo mật, phân tách hoàn toàn quyền hạn giữa Token của Người dân và Token của Quản lý.
- **Relational Database Management:**
  - Sử dụng Relationship dạng Many-to-Many giữa bảng `User` và bảng `Village`.
  - Bảng trung gian `UserVillageLink` được dùng trong PostgreSQL để lưu danh sách trạm quan tâm của từng người.
- **React State Management:**
  - Component `CitizenStations.jsx` sử dụng `useMutation` để gửi API Thêm/Xóa trạm, kèm theo hiệu ứng Optimistic UI (hiện tim đỏ ngay lập tức trước khi server trả kết quả) để tăng độ mượt mà cho trải nghiệm người dùng.

## 4. Tệp mã nguồn tham khảo
- Backend: `backend/app/api/routes/auth.py`, `backend/app/api/routes/citizen.py` (Lưu/lấy trạm yêu thích)
- Frontend: `frontend/src/pages/Register.jsx`, `frontend/src/pages/citizen/CitizenStations.jsx`
