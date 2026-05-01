# THIẾT KẾ CƠ SỞ DỮ LIỆU AIRGUARD BN

Tài liệu này chứa các câu lệnh SQL để khởi tạo cấu trúc cơ sở dữ liệu trên PostgreSQL + TimescaleDB.

---

### 1. Quản lý Người dùng (Users & Auth)
Bảng lưu trữ thông tin đăng ký của Người dân và tài khoản Nhà quản lý.

```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    role VARCHAR(50) DEFAULT 'CITIZEN', -- CITIZEN hoặc MANAGER
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 2. Quản lý Trạm Quan trắc (Stations)
Lưu trữ thông tin vị trí các trạm tại các làng nghề.

```sql
CREATE TABLE stations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    village_name VARCHAR(100), -- Ví dụ: Phong Khê, Đồng Kỵ
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    status VARCHAR(20) DEFAULT 'ONLINE', -- ONLINE, OFFLINE, MAINTENANCE
    last_update TIMESTAMP WITH TIME ZONE
);
```

### 3. Dữ liệu Cảm biến (Sensor Data - Time Series)
Bảng quan trọng nhất, lưu trữ các chỉ số ô nhiễm. Sử dụng **TimescaleDB Hypertable**.

```sql
CREATE TABLE sensor_data (
    time TIMESTAMP WITH TIME ZONE NOT NULL,
    station_id INTEGER REFERENCES stations(id),
    pm25 DOUBLE PRECISION,
    pm10 DOUBLE PRECISION,
    so2 DOUBLE PRECISION,
    no2 DOUBLE PRECISION,
    co DOUBLE PRECISION,
    o3 DOUBLE PRECISION,
    temp DOUBLE PRECISION,
    humidity DOUBLE PRECISION,
    wind_speed DOUBLE PRECISION,
    aqi_current INTEGER,
    aqi_category VARCHAR(50) -- Tốt, Trung bình, Kém, Xấu...
);

-- Biến bảng sensor_data thành Hypertable để tối ưu dữ liệu chuỗi thời gian
SELECT create_hypertable('sensor_data', 'time');
```

### 4. Dự báo AQI (AI Forecasts)
Lưu trữ kết quả từ mô hình LSTM.

```sql
CREATE TABLE forecasts (
    id SERIAL PRIMARY KEY,
    station_id INTEGER REFERENCES stations(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    target_time TIMESTAMP WITH TIME ZONE NOT NULL, -- Thời điểm 6h tới
    predicted_aqi INTEGER NOT NULL
);
```

### 5. Hệ thống Cảnh báo & Khuyến nghị (Alerts & Advice)
Lưu lịch sử cảnh báo và các khuyến nghị từ Nhà quản lý.

```sql
CREATE TABLE alerts (
    id SERIAL PRIMARY KEY,
    station_id INTEGER REFERENCES stations(id),
    time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    aqi_value INTEGER,
    alert_level VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE
);

CREATE TABLE recommendations (
    id SERIAL PRIMARY KEY,
    manager_id INTEGER REFERENCES users(id),
    village_name VARCHAR(100),
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
```

### 6. Danh sách yêu thích của Người dân (User Favorites)
Dùng để gửi thông báo cá nhân hóa.

```sql
CREATE TABLE user_favorites (
    user_id INTEGER REFERENCES users(id),
    station_id INTEGER REFERENCES stations(id),
    PRIMARY KEY (user_id, station_id)
);
```

---
### Ghi chú kỹ thuật:
1.  **Chỉ mục (Indexing):** Nên tạo index trên cột `email` của bảng `users` và `station_id` của bảng `sensor_data` để tăng tốc độ truy vấn.
2.  **TimescaleDB:** Đảm bảo extension TimescaleDB đã được cài đặt trong PostgreSQL trước khi chạy lệnh `create_hypertable`.
3.  **Dự báo:** Bảng `forecasts` giúp lưu lại lịch sử dự báo để sau này so sánh độ chính xác của AI.
