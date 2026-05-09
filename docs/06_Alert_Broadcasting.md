# 6. Phát thông báo cảnh báo (Sau kiểm duyệt)

## 1. Mục đích
Đảm bảo tính xác thực và tránh báo động giả (False Alarm) do lỗi cảm biến hoặc AI. Quy trình "Human-in-the-loop" giúp cán bộ nhà nước có quyền quyết định cuối cùng trước khi thông tin được phát tán rộng rãi cho dân chúng.

## 2. Cách hoạt động
- **Duyệt qua danh sách chờ:** Trên màn hình Cảnh báo của Admin, các cảnh báo tự động do máy sinh ra được tô viền đỏ (chưa duyệt).
- **Kiểm tra thông tin:** Admin click vào cảnh báo để xem chi tiết mốc thời gian, nồng độ AQI vượt ngưỡng bao nhiêu đơn vị.
- **Quyết định:**
  - Nếu thông tin chuẩn xác: Nhấn "Phê duyệt & Gửi". Hệ thống đổi trạng thái `is_approved = True` và cập nhật `approved_by` (Lưu dấu vết người duyệt). Cảnh báo lập tức hiển thị lên App của người dân.
  - Nếu là lỗi cảm biến: Nhấn "Xóa". Cảnh báo bị hủy khỏi DB.

## 3. Kỹ thuật & Công nghệ sử dụng
- **React AnimatePresence & Framer Motion:** Xây dựng Dialog (Popup) xác nhận duyệt/xóa với hiệu ứng mượt mà, giúp UX không bị cứng nhắc.
- **TanStack React Query (Mutations):**
  - Sử dụng `useMutation` để gửi API PATCH lên server.
  - Sau khi server báo thành công (HTTP 200), gọi `queryClient.invalidateQueries` để tự động làm mới danh sách cảnh báo mà không cần F5 trình duyệt.
- **FastAPI / SQLModel:** Endpoint `POST /alerts/approve/{id}` xử lý cập nhật cờ boolean trong database an toàn theo ACID properties.

## 4. Tệp mã nguồn tham khảo
- Frontend: `frontend/src/pages/Alerts.jsx`
- Backend: `backend/app/api/routes/alert.py`
