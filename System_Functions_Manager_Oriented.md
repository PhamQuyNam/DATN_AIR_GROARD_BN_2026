# TÀI LIỆU CHỨC NĂNG HỆ THỐNG AIRGUARD BN (TINH GỌN)
## (Định hướng: Nhà quản lý & Người dân)

Hệ thống tập trung vào giám sát thời gian thực, dự báo AI và kênh thông tin giữa nhà quản lý và cộng đồng.

---

### 1. BẢN ĐỒ GIÁM SÁT THÔNG MINH (SMART GIS DASHBOARD)
Giao diện trung tâm kết hợp giữa dữ liệu môi trường và tình trạng hạ tầng.
*   **Bản đồ AQI thời gian thực:** Hiển thị mạng lưới trạm quan trắc với mã màu chuẩn QCVN. Làm nổi bật các làng nghề đang có nguy cơ ô nhiễm cao.
*   **Trạng thái trạm:** 

### 2. PHÂN TÍCH & DỰ BÁO AI (AI PREDICTIVE ANALYTICS)
Tận dụng sức mạnh của trí tuệ nhân tạo để hỗ trợ ra quyết định.
*   **Dự báo 6h (LSTM):** Hiển thị biểu đồ xu hướng AQI trong 6 giờ tới, giúp chủ động phương án ứng phó.
*   **Giải thích nguyên nhân (SHAP):** Phân tích các yếu tố (PM2.5, gió, nhiệt độ...) đóng góp vào chỉ số AQI hiện tại, giúp nhà quản lý hiểu rõ nguồn gốc ô nhiễm.

### 3. ĐIỀU HÀNH CẢNH BÁO (INCIDENT MANAGEMENT)
Kênh tương tác trực tiếp từ cơ quan quản lý đến cộng đồng.
*   **Quản lí cảnh báo:** Hiển thị danh sách trạm kèm trạng thái Online/Offline để nhà quản lý biết trạm nào đang hoạt động tốt. Nhà quản lý thiết lập các ngưỡng an toàn. Khi AQI vượt ngưỡng, hệ thống tự động đẩy thông báo xuống người dân.
*   **Phê duyệt khuyến nghị:** Nhà quản lý cập nhật các thông điệp bảo vệ sức khỏe (đeo khẩu trang, hạn chế sản xuất...) để người dân tiếp nhận chính thống.

### 4. THỐNG KÊ (STATISTICS)
Cung cấp cái nhìn tổng thể về hiệu quả quản lý môi trường qua các con số.
*   **Thống kê :** Tổng hợp tỷ lệ phần trăm các mức độ AQI (Tốt, Trung bình, Kém...) theo tháng/quý để đánh giá xu hướng cải thiện môi trường. Xếp hạng các khu vực/làng nghề có chỉ số AQI cao nhất hoặc thấp nhất trong kỳ để nhà quản lý ưu tiên nguồn lực xử lý.

### 5. GIAO DIỆN DÀNH CHO CỘNG ĐỒNG (PUBLIC PORTAL)
Kênh thụ hưởng thông tin dành cho người dân.
*   **Xem thông tin:** Người dân xem bản đồ AQI và kết quả dự báo 6h để chủ động kế hoạch sinh hoạt.
*   **Nhận cảnh báo & Khuyến nghị:** Sau khi đăng nhập và chọn các trạm quan trắc "yêu thích", người dân sẽ tự động nhận được toàn bộ thông báo đẩy, cảnh báo ô nhiễm và lời khuyên sức khỏe từ nhà quản lý riêng cho các khu vực đã chọn đó.

### 6. CỔNG ĐĂNG KÝ CHO NGƯỜI DÂN (CITIZEN AUTH)
Cho phép người dân tham gia vào mạng lưới nhận tin của hệ thống.
*   **Đăng ký tài khoản người dân:** Người dân tự đăng ký tài khoản để có thể thiết lập các tính năng cá nhân hóa.
*   **Trạm quan tâm:** Người dân có quyền chọn và lưu danh sách các trạm quan trắc tại khu vực mình sinh sống hoặc quan tâm để tối ưu hóa việc nhận tin cảnh báo.

---
**Đội ngũ phát triển AirGuard BN - 2026**
