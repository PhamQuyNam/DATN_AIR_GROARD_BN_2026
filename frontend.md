# KẾ HOẠCH CHI TIẾT PHÁT TRIỂN FRONTEND AIRGUARD BN

Tài liệu này hướng dẫn cách tổ chức mã nguồn trong thư mục `frontend/src/` để xây dựng giao diện tương tác cho dự án, sử dụng ReactJS, Tailwind CSS và các thư viện đồ họa chuyên sâu.

---

## 1. Cấu trúc thư mục đề xuất (Dựa trên React + Vite)
```text
frontend/src/
├── components/      # Các thành phần tái sử dụng (Button, Card, Input)
│   ├── Map/         # Hợp phần bản đồ Mapbox/Leaflet
│   ├── Charts/      # Biểu đồ LSTM & SHAP
│   └── Layout/      # Navbar, Sidebar cho Admin/Public
├── pages/           # Các trang giao diện chính
│   ├── Dashboard.jsx    # Bản đồ thời gian thực
│   ├── Details.jsx      # Phân tích sâu (Dự báo & SHAP)
│   ├── Admin/           # Trang dành cho nhà quản lý
│   ├── Auth/            # Đăng nhập & Đăng ký người dân
│   └── Statistics.jsx   # Tra cứu lịch sử & Báo cáo
├── services/        # Gọi API từ Backend (Sử dụng Axios)
├── hooks/           # Custom hooks (e.g., useAQIData)
└── store/           # Quản lý trạng thái (Zustand hoặc Context API)
```

---

## 2. Các trang giao diện cần xây dựng chi tiết

### Trang 1: Bản đồ giám sát (Dashboard)
*   **Chức năng:** Hiển thị toàn cảnh các làng nghề Bắc Ninh.
*   **Thành phần chính:**
    *   `MapContainer`: Tích hợp Mapbox GL JS. Hiển thị các Marker màu (Xanh, Vàng, Đỏ) dựa trên chỉ số AQI.
    *   `AQILegend`: Bảng chú giải các mức độ ô nhiễm theo QCVN.
    *   `StationSummary`: Khi click vào Marker, hiện một Popup tóm tắt nồng độ bụi PM2.5.

### Trang 2: Chi tiết trạm & Phân tích AI (Details)
*   **Chức năng:** Giải thích lý do ô nhiễm (SHAP) và dự báo xu hướng (LSTM).
*   **Thành phần chính:**
    *   `ForecastChart`: Sử dụng **Recharts** hoặc **Chart.js** để vẽ biểu đồ đường thể hiện AQI trong 6 giờ tới (dữ liệu từ mô hình LSTM).
    *   `ExplanationChart`: Biểu đồ cột ngang (Bar Chart) hiển thị giá trị SHAP (ví dụ: Gió ảnh hưởng -10%, PM2.5 ảnh hưởng +30%).

### Trang 3: Cổng Đăng ký & Đăng nhập (Auth)
*   **Chức năng:** Dành cho người dân để nhận thông báo cá nhân.
*   **Thành phần chính:**
    *   Form đăng ký với các trường: Họ tên, Email, Mật khẩu.
    *   Logic lưu **JWT Token** vào LocalStorage để duy trì phiên đăng nhập.

### Trang 4: Quản lý dành cho Nhà quản lý (Admin Panel)
*   **Chức năng:** Điều hành và cấu hình hệ thống.
*   **Thành phần chính:**
    *   `StationManager`: Bảng (Table) hiển thị trạng thái Online/Offline của các cảm biến.
    *   `AlertConfig`: Form điều chỉnh các ngưỡng AQI để kích hoạt cảnh báo đỏ.
    *   `RecommendationEditor`: Trình soạn thảo văn bản để gửi khuyến nghị sức khỏe xuống ứng dụng người dân.

### Trang 5: Thống kê (Statistics Dashboard)
*   **Chức năng:** Cung cấp cái nhìn tổng quan về tình hình môi trường qua các biểu đồ phân tích.
*   **Thành phần chính:**
    *   `AQIPieChart`: Biểu đồ tròn hiển thị tỷ lệ % (Tốt, Trung bình, Kém...) trong một khoảng thời gian.
    *   `RankingTable`: Bảng xếp hạng mức độ ô nhiễm giữa các làng nghề (Top ô nhiễm nhất).
    *   `PeriodSelector`: Bộ lọc chọn xem thống kê theo Tuần, Tháng hoặc Năm.

---

## 3. Công nghệ chủ đạo đề xuất
*   **Styling:** Tailwind CSS (giúp giao diện hiện đại và nhanh chóng).
*   **Map:** `react-map-gl` (nếu dùng Mapbox) hoặc `react-leaflet`.
*   **Charts:** `Recharts` (rất dễ tùy biến và đẹp cho React).
*   **Icons:** `Lucide React` hoặc `HeroIcons`.

---

## 4. Lộ trình thực hiện Frontend
1.  **Bước 1:** Cấu hình `Axios` và kết nối thử với Backend API.
2.  **Bước 2:** Xây dựng phần Bản đồ (Dashboard) - đây là linh hồn của đồ án.
3.  **Bước 3:** Xây dựng trang Chi tiết và vẽ các biểu đồ AI (LSTM, SHAP).
4.  **Bước 4:** Xây dựng trang Đăng nhập và phân quyền hiển thị (Admin vs Public).
5.  **Bước 5:** Hoàn thiện giao diện Cảnh báo và Thống kê.
