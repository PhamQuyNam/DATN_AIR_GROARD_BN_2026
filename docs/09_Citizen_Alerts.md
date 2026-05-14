# 9. Tiếp nhận cảnh báo & Khuyến nghị (Giao diện Người dân)

## 1. Mục đích
Chức năng trọng tâm của Cổng Người dân. Giúp người dân nhận được tin tức ô nhiễm khẩn cấp một cách kịp thời, minh bạch để chủ động phòng tránh rủi ro sức khỏe.

## 2. Cách hoạt động
- Trình duyệt của người dân liên tục gọi API ngầm (mỗi 30 giây) lên máy chủ để hỏi danh sách Feed mới nhất.
- Backend chỉ trả về các Cảnh báo có cờ `is_approved = True` (đã được Sở duyệt) và các Khuyến nghị chung.
- Nếu Backend trả về số lượng bài báo nhiều hơn số bài báo mà người dân "đã xem lần cuối" (Last Seen), giao diện sẽ hiển thị một Notification Badge (Chấm đỏ nhấp nháy trên biểu tượng chuông).
- Khi người dân click vào tab "Cảnh báo", chấm đỏ tự động biến mất và lưu thời gian xem cuối cùng vào trình duyệt.

## 3. Kỹ thuật & Công nghệ sử dụng
- **React Query (Polling):** 
  - Cấu hình `refetchInterval: 30000`. Cơ chế Long-polling giả lập WebSockets giúp cập nhật dữ liệu Real-time mà không cần cài đặt hạ tầng phức tạp.
- **Local Storage State:** 
  - Sử dụng `localStorage` trình duyệt để ghi nhớ giá trị `citizen_alerts_last_seen`. Giúp giữ trạng thái "Đã đọc" của chuông thông báo ngay cả khi người dân tắt tab web đi mở lại.
- **API Filtering (Backend):** 
  - Luôn đi kèm `WHERE is_approved = True` trong logic Query của SQLModel để đảm bảo dân không bao giờ đọc được thông báo thô từ AI chưa qua kiểm duyệt.

## 4. Tệp mã nguồn tham khảo
- Frontend: `frontend/src/pages/citizen/CitizenAlerts.jsx`, `frontend/src/components/Layout/CitizenLayout.jsx`
- Backend: `backend/app/api/routes/citizen.py`
