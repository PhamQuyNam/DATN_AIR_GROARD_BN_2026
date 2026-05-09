# 5. Quản lý cảnh báo (Alert & System Management)

## 1. Mục đích
Cho phép cơ quan quản lý (Admin) thiết lập tự động hóa quy trình giám sát môi trường. Thiết lập "Ranh giới đỏ" cho từng làng nghề, hệ thống sẽ tự động bắt lỗi khi có vi phạm tiêu chuẩn.

## 2. Cách hoạt động
- **Cấu hình ngưỡng:** Cán bộ truy cập danh sách trạm, bấm "Chỉnh sửa" để cài đặt Ngưỡng AQI an toàn (ví dụ Đồng Kỵ là 150, Đa Hội là 200 tùy đặc thù).
- **Lắng nghe tự động:** Background job chạy liên tục 5 phút/lần. Nó lấy dữ liệu AQI thực tế mới nhất so sánh với ngưỡng vừa cài.
- **Tạo cảnh báo nháp:** Nếu AQI > Ngưỡng, hệ thống tự động ghi một bản ghi vào bảng `AlertHistory` với trạng thái `is_approved = False` (Chờ duyệt).

## 3. Kỹ thuật & Công nghệ sử dụng
- **Backend Background Scheduler:**
  - Sử dụng thư viện `APScheduler` chạy ngầm độc lập với luồng API chính của FastAPI.
  - Trigger hàm `check_and_create_alerts` mỗi 5 phút một lần.
- **Quản lý trạng thái DB (SQLModel):**
  - Tách biệt hai bảng: `AlertConfig` (Lưu ngưỡng cố định của trạm) và `AlertHistory` (Lưu lịch sử các lần vượt ngưỡng).
- **Giao diện quản lý:**
  - React hook `useState` để quản lý trạng thái chỉnh sửa inline trực tiếp trên bảng danh sách làng nghề.

## 4. Tệp mã nguồn tham khảo
- Backend: `backend/app/scheduler/jobs.py`, `backend/app/services/alert_service.py`
- Frontend: `frontend/src/pages/Alerts.jsx`
