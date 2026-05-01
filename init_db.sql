-- TÀI LIỆU KHỞI TẠO DATABASE AIRGUARD BN
-- Hướng dẫn: Mở pgAdmin 4 -> Chuột phải vào Database -> Query Tool -> Dán code này -> Nhấn F5

-- 0. Bật tiện ích mở rộng TimescaleDB (Yêu cầu phải cài TimescaleDB)
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- 1. Bảng Người dùng
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    full_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    hashed_password TEXT NOT NULL,
    role VARCHAR(50) DEFAULT 'CITIZEN',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. Bảng Trạm quan trắc
CREATE TABLE IF NOT EXISTS stations (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    village_name VARCHAR(100),
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    status VARCHAR(20) DEFAULT 'ONLINE',
    last_update TIMESTAMP WITH TIME ZONE
);

-- 3. Bảng Dữ liệu cảm biến (Time-series)
CREATE TABLE IF NOT EXISTS sensor_data (
    time TIMESTAMP WITH TIME ZONE NOT NULL,
    station_id INTEGER REFERENCES stations(id) ON DELETE CASCADE,
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
    aqi_category VARCHAR(50)
);

-- Chuyển thành Hypertable (Bỏ qua nếu chưa cài TimescaleDB, nhưng khuyến khích có)
SELECT create_hypertable('sensor_data', 'time', if_not_exists => TRUE);

-- 4. Bảng Dự báo AI
CREATE TABLE IF NOT EXISTS forecasts (
    id SERIAL PRIMARY KEY,
    station_id INTEGER REFERENCES stations(id) ON DELETE CASCADE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    target_time TIMESTAMP WITH TIME ZONE NOT NULL,
    predicted_aqi INTEGER NOT NULL
);

-- 5. Bảng Cảnh báo
CREATE TABLE IF NOT EXISTS alerts (
    id SERIAL PRIMARY KEY,
    station_id INTEGER REFERENCES stations(id) ON DELETE CASCADE,
    time TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    aqi_value INTEGER,
    alert_level VARCHAR(50),
    is_active BOOLEAN DEFAULT TRUE
);

-- 6. Bảng Khuyến nghị của Nhà quản lý
CREATE TABLE IF NOT EXISTS recommendations (
    id SERIAL PRIMARY KEY,
    manager_id INTEGER REFERENCES users(id),
    village_name VARCHAR(100),
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 7. Bảng Yêu thích (Personalization)
CREATE TABLE IF NOT EXISTS user_favorites (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    station_id INTEGER REFERENCES stations(id) ON DELETE CASCADE,
    PRIMARY KEY (user_id, station_id)
);

-- 8. Tạo Index để tối ưu truy vấn
CREATE INDEX IF NOT EXISTS idx_sensor_data_station ON sensor_data(station_id, time DESC);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_stations_village ON stations(village_name);

-- THÀNH CÔNG: Database đã sẵn sàng sử dụng.
