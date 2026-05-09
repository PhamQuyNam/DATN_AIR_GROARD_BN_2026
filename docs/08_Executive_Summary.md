# 8. Thống kê AQI (Executive Summary)

## 1. Mục đích
Cung cấp cái nhìn tổng quan dạng báo cáo quản trị (Dashboard Analytics) cho ban lãnh đạo. Giúp đánh giá xu hướng môi trường theo thời gian dài (tuần/tháng) để lập kế hoạch hoặc báo cáo lên cấp cao hơn.

## 2. Cách hoạt động
- Hệ thống backend truy xuất toàn bộ dữ liệu lịch sử trong cơ sở dữ liệu.
- Tính toán tần suất xuất hiện của các mức độ AQI (Tốt, Trung Bình, Kém, Xấu...).
- Phân nhóm dữ liệu theo từng làng nghề hoặc theo mốc thời gian.
- Giao diện Frontend hiển thị kết quả qua các biểu đồ tròn (Pie Chart) biểu diễn cơ cấu chất lượng, và biểu đồ cột (Bar Chart) để so sánh các trạm với nhau.

## 3. Kỹ thuật & Công nghệ sử dụng
- **Data Aggregation (Backend):**
  - Sử dụng các câu lệnh `GROUP BY` và hàm tổng hợp (Aggration functions) của SQL trực tiếp qua SQLModel/SQLAlchemy để tránh tải lượng dữ liệu khổng lồ về RAM của Python.
- **Data Visualization (Frontend):**
  - **Recharts:** Thư viện vẽ biểu đồ chuyên nghiệp. 
  - `PieChart`: Render tỷ lệ phần trăm chất lượng không khí.
  - `BarChart`: Vẽ biểu đồ cột xếp hạng top các làng nghề ô nhiễm nhất.

## 4. Tệp mã nguồn tham khảo
- Frontend: `frontend/src/pages/Analytics.jsx`
- Backend: `backend/app/api/routes/analytics.py`
