# 2. Theo dõi trạng thái trạm (Station Monitoring)

## 1. Mục đích
Hỗ trợ cán bộ quản lý kỹ thuật giám sát "sức khỏe" và tình trạng kết nối của các trạm đo lường môi trường tự động đặt tại các làng nghề.

## 2. Cách hoạt động
- Hệ thống backend liên tục cập nhật timestamp (thời gian) mỗi khi nhận được luồng dữ liệu mới từ các trạm đo (thông qua API hoặc luồng crawl từ Open-Meteo).
- Giao diện Admin gửi yêu cầu kiểm tra danh sách các trạm.
- Hệ thống so sánh thời gian nhận dữ liệu cuối cùng của trạm với thời gian hiện tại.
- Nếu thời gian trễ quá một ngưỡng cho phép (ví dụ > 2 giờ), hệ thống đánh dấu trạm đó là "Mất kết nối" (Offline) hoặc "Bất thường" (Error). Nếu vẫn gửi đều, đánh dấu là "Bình thường" (Online).

## 3. Kỹ thuật & Công nghệ sử dụng
- **Kỹ thuật Heartbeat / Time-diff:** Dùng độ trễ thời gian (Timestamp diffing) giữa bản ghi cuối cùng trong cơ sở dữ liệu và thời gian hệ thống (System Time) để tính toán trạng thái mạng/kết nối của cảm biến.
- **Frontend:**
  - **React Data Tables:** Render danh sách các trạm dưới dạng bảng tính có thể sort/filter.
  - **Lucide Icons:** Cung cấp các icon minh họa trạng thái (Tích xanh, Dấu X đỏ).
- **Backend:**
  - **FastAPI Endpoint:** Cung cấp API trả về metadata của `Village` kết hợp thời gian đo gần nhất trong bảng `AQILog`.
  - **PostgreSQL Database:** Lưu trữ thông tin địa lý và cấu hình của từng trạm đo lường.

## 4. Tệp mã nguồn tham khảo
- Frontend: `frontend/src/pages/StationStatus.jsx`
- Backend: `backend/app/models/db_models.py` (Bảng Village & AQILog)
