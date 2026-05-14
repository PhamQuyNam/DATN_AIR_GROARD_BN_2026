# TỔNG QUAN CHỨC NĂNG DỰ ÁN AIRGUARD BN

Tài liệu này mô tả 10 chức năng cốt lõi của hệ thống, được chia làm 2 phân hệ chính: Dành cho Cán bộ Quản lý và Dành cho Người dân.

---

## PHẦN I: DÀNH CHO CÁN BỘ QUẢN LÝ (ADMIN )

### 1. Bản đồ AQI thời gian thực (GIS Dashboard)
- **Mô tả:** Màn hình chính của ban quản lý. Cung cấp một bản đồ số GIS trực quan hiển thị vị trí của toàn bộ các làng nghề trên địa bàn tỉnh.
- **Hoạt động:** Các điểm trên bản đồ được biểu diễn bằng màu sắc cảnh báo (Xanh, Vàng, Cam, Đỏ) dựa trên chỉ số AQI thực tế tại thời điểm hiện tại. Khi click vào một điểm, quản lý có thể xem nhanh các chỉ số chi tiết (Nhiệt độ, Độ ẩm, Bụi PM2.5, PM10...).

### 2. Theo dõi trạng thái trạm (Station Monitoring)
- **Mô tả:** Chức năng giám sát "sức khỏe" của các trạm đo lường môi trường (cảm biến).
- **Hoạt động:** Giúp cán bộ biết được trạm nào đang hoạt động tốt (Online), trạm nào đang mất kết nối hoặc gửi về dữ liệu bất thường (Offline/Lỗi), từ đó có phương án bảo trì kịp thời.

### 3. Dự báo AQI 6 giờ (LSTM Forecast)
- **Mô tả:** Ứng dụng Trí tuệ nhân tạo (AI) để dự đoán chất lượng không khí trong tương lai gần.
- **Hoạt động:** Sử dụng mô hình học sâu LSTM, hệ thống dự báo sự biến động của chỉ số AQI trong 1 đến 6 giờ tiếp theo. Giao diện hiển thị dưới dạng biểu đồ đường, giúp cán bộ có thể chủ động ra quyết định trước khi ô nhiễm thực sự xảy ra.

### 4. Giải thích nguyên nhân (SHAP Interpretation)
- **Mô tả:** Chức năng "giải thích" kết quả của AI, giúp kết quả dự báo trở nên minh bạch và đáng tin cậy.
- **Hoạt động:** Áp dụng kỹ thuật XAI (SHAP), hệ thống bóc tách và vẽ biểu đồ thể hiện mức độ đóng góp của từng yếu tố gây ô nhiễm (Ví dụ: Sự gia tăng của bụi mịn PM2.5 làm tăng ô nhiễm, trong khi sức gió mạnh giúp giảm ô nhiễm).

### 5. Quản lý cảnh báo (Alert & System Management)
- **Mô tả:** Nơi thiết lập và quản lý các luồng cảnh báo tự động.
- **Hoạt động:** Cán bộ có thể chủ động cài đặt "ngưỡng an toàn" (Ví dụ: AQI > 150) cho từng làng nghề riêng biệt. Hệ thống cứ mỗi 5 phút sẽ tự động quét dữ liệu, nếu phát hiện vượt ngưỡng sẽ tự động sinh ra một "Cảnh báo chờ duyệt".

### 6. Phát thông báo cảnh báo (Sau kiểm duyệt)
- **Mô tả:** Quy trình con người tham gia kiểm soát trước khi thông tin đến tay dân.
- **Hoạt động:** Thay vì AI tự động gửi báo động cho dân (dễ gây hoang mang nếu AI sai), các "Cảnh báo chờ duyệt" sẽ được hiển thị cho cán bộ. Cán bộ có quyền đọc, xác minh, sau đó bấm nút **[Phê duyệt & Gửi]** hoặc **[Xóa]**. Chỉ khi được phê duyệt, cảnh báo mới tới tay dân.

### 7. Phê duyệt & Đẩy khuyến nghị sức khỏe
- **Mô tả:** Cổng thông tin giao tiếp một chiều từ chính quyền xuống người dân.
- **Hoạt động:** Cán bộ có thể chủ động soạn thảo và đăng tải các đoạn văn bản "Khuyến nghị" (Ví dụ: Hướng dẫn người già và trẻ em đeo khẩu trang, hạn chế tập thể dục buổi sáng). Các khuyến nghị này sẽ được đẩy thẳng xuống app của dân.

### 8. Thống kê AQI (Executive Summary)
- **Mô tả:** Màn hình báo cáo tổng hợp dành cho lãnh đạo.
- **Hoạt động:** Cung cấp các biểu đồ thống kê (cột, tròn) về mức độ ô nhiễm theo thời gian, tỷ lệ các mức độ AQI (Tốt, Xấu, Nguy hại) trong ngày/tuần/tháng để làm tư liệu lập báo cáo môi trường.

---

## PHẦN II: DÀNH CHO NGƯỜI DÂN (CITIZEN PORTAL)

### 9. Tiếp nhận cảnh báo & Khuyến nghị (Giao diện Người dân)
*(Ghi chú: Đánh số 9 và 10 để thứ tự liền mạch với chức năng 10, 11 của yêu cầu)*
- **Mô tả:** Bảng tin khẩn cấp cá nhân hóa.
- **Hoạt động:** Giao diện có chuông thông báo màu đỏ tự động nhấp nháy (Polling ngầm 30s/lần) khi có Cảnh báo hoặc Khuyến nghị mới vừa được cán bộ phê duyệt. Người dân đọc được các tin tức môi trường chính xác và có tính xác thực cao từ cơ quan quản lý.

### 10. Đăng ký & Trạm quan tâm (Dành cho Người dân)
- **Mô tả:** Tính năng cá nhân hóa trải nghiệm theo dõi môi trường.
- **Hoạt động:** Người dân có thể đăng ký tài khoản và thiết lập theo dõi các làng nghề cụ thể (Ví dụ: Quê hương, nơi làm việc). Hệ thống sẽ ưu tiên hiển thị chỉ số của các trạm "Yêu thích" này ngay trên màn hình chính của họ, tránh việc bị ngợp thông tin bởi các trạm không liên quan.
