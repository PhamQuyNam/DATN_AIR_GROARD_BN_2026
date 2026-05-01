# KẾ HOẠCH CHI TIẾT PHÁT TRIỂN BACKEND AIRGUARD BN

Tài liệu này hướng dẫn cách cấu trúc lại và bổ sung các file trong thư mục `backend/app/` để đáp ứng các yêu cầu chức năng dành cho Nhà quản lý và Người dân.

---

## 1. Cấu trúc thư mục đề xuất (Dựa trên FastAPI)
Bạn nên tổ chức code theo mô hình Service-Oriented để dễ bảo trì:
```text
backend/app/
├── api/             # Nơi chứa các Route (Endpoints)
│   └── v1/
│       ├── auth.py         # Đăng ký/Đăng nhập người dân
│       ├── map.py          # Dữ liệu bản đồ & Trạm
│       ├── analytics.py    # Dự báo AI & SHAP
│       ├── alerts.py       # Cảnh báo & Khuyến nghị
│       └── history.py      # Truy vấn lịch sử & Thống kê
├── core/            # Cấu hình hệ thống (DB, Security)
├── models/          # Khai báo SQLModel tương ứng với các bảng SQL
├── schemas/         # Pydantic schemas để validate dữ liệu đầu vào/ra
├── services/        # Logic nghiệp vụ (Nơi gọi model AI, tính AQI)
└── main.py          # File khởi chạy chính
```

---

## 2. Mô tả chi tiết các Service & Danh sách API

### 2.1. AuthService (Dịch vụ xác thực)
*   **Mô tả:** Chịu trách nhiệm quản lý tài khoản người dân, mã hóa mật khẩu và cấp phát JWT Token để truy cập các tính năng cá nhân hóa.
*   **Danh sách API:**

| Phương thức | Endpoint | Chức năng | Đối tượng |
| :--- | :--- | :--- | :--- |
| **POST** | `/auth/register` | Đăng ký tài khoản người dân mới | Người dân |
| **POST** | `/auth/login` | Đăng nhập và nhận Token xác thực | Chung |
| **GET** | `/auth/me` | Lấy thông tin tài khoản hiện tại | Chung |
| **POST** | `/auth/favorites` | Thêm trạm vào danh sách quan tâm | Người dân |
| **GET** | `/auth/favorites` | Xem danh sách trạm đang quan tâm | Người dân |
| **DELETE** | `/auth/favorites/{id}`| Xóa trạm khỏi danh sách quan tâm | Người dân |

### 2.2. MapService (Dịch vụ Bản đồ & Trạm)
*   **Mô tả:** Xử lý việc tính toán AQI tức thời và theo dõi trạng thái hoạt động của mạng lưới trạm cảm biến tại các làng nghề.
*   **Danh sách API:**

| Phương thức | Endpoint | Chức năng | Đối tượng |
| :--- | :--- | :--- | :--- |
| **GET** | `/map/stations` | Lấy danh sách trạm kèm tọa độ và màu AQI | Chung |
| **GET** | `/map/stations/{id}` | Xem chi tiết nồng độ các chất tại 1 trạm | Chung |
| **GET** | `/map/status` | Xem danh sách trạng thái Online/Offline | Quản lý |

### 2.3. AIService (Dịch vụ Phân tích & Dự báo AI)
*   **Mô tả:** Tích hợp mô hình LSTM để dự báo tương lai và XGBoost/SHAP để giải thích nguyên nhân ô nhiễm.
*   **Danh sách API:**

| Phương thức | Endpoint | Chức năng | Đối tượng |
| :--- | :--- | :--- | :--- |
| **GET** | `/analytics/forecast/{id}` | Lấy dữ liệu dự báo AQI 6h tới (LSTM) | Chung |
| **GET** | `/analytics/explain/{id}` | Lấy giá trị đóng góp SHAP của các yếu tố | Chung |

### 2.4. AlertService (Dịch vụ Cảnh báo & Khuyến nghị)
*   **Mô tả:** Kiểm tra ngưỡng ô nhiễm, tự động kích hoạt trạng thái cảnh báo và quản lý các nội dung tư vấn sức khỏe. Hệ thống sẽ lọc danh sách người dân theo dõi trạm ô nhiễm để gửi thông báo đẩy (Push Notification) chính xác.
*   **Danh sách API:**

| Phương thức | Endpoint | Chức năng | Đối tượng |
| :--- | :--- | :--- | :--- |
| **GET** | `/alerts/active` | Danh sách các khu vực đang bị cảnh báo | Chung |
| **PATCH** | `/alerts/config` | Cấu hình lại các ngưỡng AQI (QCVN) | Quản lý |
| **POST** | `/alerts/recommend` | Phê duyệt và đẩy khuyến nghị xuống dân | Quản lý |
| **GET** | `/alerts/recommend/{village}` | Xem lời khuyên của chuyên gia cho khu vực | Người dân |

### 2.5. StatisticsService (Dịch vụ Thống kê)
*   **Mô tả:** Tổng hợp dữ liệu từ TimescaleDB để tạo ra các báo cáo phân tích về tỷ lệ ô nhiễm và xếp hạng khu vực.
*   **Danh sách API:**

| Phương thức | Endpoint | Chức năng | Đối tượng |
| :--- | :--- | :--- | :--- |
| **GET** | `/statistics/aqi-distribution` | Lấy tỷ lệ % các mức AQI (Pie Chart) | Chung |
| **GET** | `/statistics/rankings` | Lấy bảng xếp hạng ô nhiễm các làng nghề | Quản lý |

---

## 3. Lộ trình thực hiện (Roadmap)
1.  **Giai đoạn 1 (Kết nối):** Hoàn thiện `core/database.py` để kết nối tới PostgreSQL.
2.  **Giai đoạn 2 (Dữ liệu):** Viết `collector_service.py` để ingest dữ liệu định kỳ.
3.  **Giai đoạn 3 (Tính toán):** Hoàn thiện `MapService` để hiển thị bản đồ.
4.  **Giai đoạn 4 (AI Integration):** Nhúng model LSTM và XGBoost vào `AIService`.
5.  **Giai đoạn 5 (Auth & Alert):** Xây dựng hệ thống đăng ký và đẩy thông báo.

---
**Lời khuyên:** Hãy bắt đầu từ `models/` để định nghĩa cấu trúc dữ liệu, sau đó viết `schemas/` để quy định kiểu dữ liệu cho các API.
