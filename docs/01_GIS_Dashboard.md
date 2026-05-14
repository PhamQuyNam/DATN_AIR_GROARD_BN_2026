# 1. Bản đồ AQI thời gian thực (GIS Dashboard)

## 1. Mục đích
Cung cấp cái nhìn tổng quan toàn cảnh về chất lượng không khí tại các làng nghề trên địa bàn tỉnh Bắc Ninh. Dành riêng cho cán bộ quản lý (Admin/Manager) theo dõi trực quan trạng thái môi trường.

## 2. Cách hoạt động
- **Hiển thị bản đồ:** Tải bản đồ địa lý dựa trên tọa độ thực của các làng nghề.
- **Biểu diễn dữ liệu:** Dữ liệu cảm biến mới nhất (AQI, PM2.5, PM10, Nhiệt độ...) của mỗi làng nghề được fetch từ backend và hiển thị thành các điểm đánh dấu (marker) trên bản đồ.
- **Phân loại màu sắc:** Marker tự động đổi màu theo chuẩn AQI (Xanh: Tốt, Vàng: Trung bình, Đỏ: Xấu...) để cán bộ dễ dàng nhận diện vùng nguy hiểm.
- **Tương tác:** Click vào một marker sẽ mở ra tooltip/popup chứa các chỉ số môi trường chi tiết tại thời điểm hiện tại của khu vực đó.

## 3. Kỹ thuật & Công nghệ sử dụng
- **Frontend (Giao diện):** 
  - **React & Tailwind CSS:** Xây dựng khung giao diện chuẩn và responsive.
  - **Leaflet / React-Leaflet:** Thư viện bản đồ số mã nguồn mở (GIS) dùng để render bản đồ tương tác và gắn marker tọa độ.
  - **React Query:** Xử lý việc gọi API lấy dữ liệu trạm đo mới nhất và caching.
- **Backend (Xử lý):**
  - **FastAPI:** Cung cấp API endpoint `/api/v1/aqi/latest` trả về danh sách các điểm đo hiện tại.
  - **SQLAlchemy:** Truy vấn dữ liệu thực tế lưu trong bảng `AQILog` của PostgreSQL.

## 4. Tệp mã nguồn tham khảo
- Frontend: `frontend/src/pages/Dashboard.jsx`
- Backend: `backend/app/api/routes/aqi.py`
