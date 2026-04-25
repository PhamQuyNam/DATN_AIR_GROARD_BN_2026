# Tài liệu mô tả dự án DATN Air GROARD BN 2026

## Mục lục

1. [ETL Pipeline](#etl-pipeline)
   - [Ingestion (Thu thập dữ liệu)](#1-ingestion-thu-thập-dữ-liệu)
   - [Processing (Xử lý dữ liệu)](#2-processing-xử-lý-dữ-liệu)
   - [Scheduler (Lập lịch)](#3-scheduler-lập-lịch)
2. [ML Training (Huấn luyện mô hình)](#ml-training-huấn-luyện-mô-hình)
   - [Preprocessing (Tiền xử lý)](#1-preprocessing-tiền-xử-lý)
   - [Models (Mô hình)](#2-models-mô-hình)
   - [Evaluation (Đánh giá)](#3-evaluation-đánh-giá)

---

## ETL Pipeline

### 1. Ingestion (Thu thập dữ liệu)

#### `etl/ingestion/openmeteo_air_fetcher.py`

| Thuộc tính | Mô tả |
|------------|-------|
| **Công dụng** | Thu thập dữ liệu chất lượng không khí (Air Quality) từ Open-Meteo Air Quality API |
| **API Endpoint** | `https://air-quality-api.open-meteo.com/v1/air-quality` |
| **API Key** | Không cần (miễn phí cho nghiên cứu) |

**Các phương thức:**

| Phương thức | Mô tả | Đầu vào | Đầu ra |
|-------------|-------|---------|--------|
| `fetch_air_quality(village, start_date, end_date)` | Lấy dữ liệu lịch sử AQI cho 1 làng nghề | `village: dict` (name, lat, lon), `start_date: str`, `end_date: str` | `pd.DataFrame` với các cột: timestamp, village, pm25, pm10, co, no2, so2, o3, aqi_eu, us_aqi |
| `fetch_air_quality_forecast(village, forecast_days)` | Lấy dự báo AQI N ngày tới | `village: dict`, `forecast_days: int` (mặc định 5) | `pd.DataFrame` dự báo AQI |
| `collect_all_air_history(start_date, end_date)` | Thu thập AQI lịch sử cho tất cả 17 làng nghề | `start_date`, `end_date` | `pd.DataFrame` gộp tất cả làng |

**Đặc điểm:**
- Hỗ trợ retry với exponential backoff khi gặp rate limit (429)
- Tự động loại trừ làng baseline (Vọng Nguyệt)
- Mapping tên biến API → tên cột trong DB

---

#### `etl/ingestion/openmeteo_weather_fetcher.py`

| Thuộc tính | Mô tả |
|------------|-------|
| **Công dụng** | Thu thập dữ liệu thời tiết từ Open-Meteo |
| **API Endpoints** | - Archive: `https://archive-api.open-meteo.com/v1/archive` (lịch sử từ 1940)<br>- Forecast: `https://api.open-meteo.com/v1/forecast` (7-16 ngày tới) |
| **API Key** | Không cần (miễn phí) |

**Các phương thức:**

| Phương thức | Mô tả | Đầu vào | Đầu ra |
|-------------|-------|---------|--------|
| `fetch_weather_history(village, start_date, end_date)` | Lấy dữ liệu thời tiết lịch sử | `village: dict`, `start_date`, `end_date` | `pd.DataFrame` với: timestamp, temperature, humidity, wind_speed, wind_dir, precipitation, pressure, cloud_cover |
| `fetch_weather_forecast(village, forecast_days)` | Lấy dự báo thời tiết | `village: dict`, `forecast_days: int` (mặc định 7) | `pd.DataFrame` dự báo thời tiết |
| `collect_all_weather_history(start_date, end_date)` | Thu thập thời tiết cho tất cả làng | `start_date`, `end_date` | `pd.DataFrame` gộp |

**Đặc điểm:**
- Dữ liệu lịch sử từ năm 1940 → phù hợp cho dataset dài hạn
- Retry logic với exponential backoff
- Delay 3.5s giữa các request để tránh rate limit

---

### 2. Processing (Xử lý dữ liệu)

#### `etl/processing/cleaner.py`

| Thuộc tính | Mô tả |
|------------|-------|
| **Công dụng** | Làm sạch dataset sau khi merge air quality + weather |
| **Xử lý** | Missing values, outlier, kiểu dữ liệu, duplicate |

**Các phương thức:**

| Phương thức | Mô tả |
|-------------|-------|
| `clean_dataset(df)` | Pipeline làm sạch hoàn chỉnh (8 bước) |
| `_check_required_columns(df)` | Kiểm tra cột bắt buộc: timestamp, village, pm25 |
| `_cast_types(df)` | Chuẩn hóa kiểu dữ liệu (timestamp → UTC-aware, numeric → float) |
| `_remove_duplicates(df)` | Loại bỏ hàng trùng timestamp + village |
| `_drop_all_aqi_missing(df)` | Loại hàng không có bất kỳ chỉ số AQI nào |
| `_replace_outliers_with_nan(df)` | Thay outlier ngoài ngưỡng VALID_RANGES bằng NaN |
| `_interpolate_missing(df)` | Nội suy missing values (limit 3 giờ liên tiếp) |
| `_drop_remaining_missing_pm25(df)` | Loại hàng vẫn thiếu pm25 sau nội suy |
| `_add_derived_features(df)` | Thêm features: hour, day_of_week, month, is_weekend, is_rush_hour, wind_sin, wind_cos, pm25_category |

**Ngưỡng hợp lệ (VALID_RANGES):**
- PM2.5: 0-1000 µg/m³
- PM10: 0-2000 µg/m³
- Temperature: -10-50°C
- Humidity: 0-100%
- Wind speed: 0-50 m/s
- Pressure: 900-1100 hPa

---

#### `etl/processing/merger.py`

| Thuộc tính | Mô tả |
|------------|-------|
| **Công dụng** | Ghép dữ liệu air quality + thời tiết theo timestamp + village |

**Phương thức:**

| Phương thức | Mô tả | Đầu vào | Đầu ra |
|-------------|-------|---------|--------|
| `merge_air_and_weather(df_air, df_weather)` | Ghép 2 DataFrame theo timestamp + village | `df_air: pd.DataFrame`, `df_weather: pd.DataFrame` | `pd.DataFrame` đã merge và sắp xếp cột |

**Đặc điểm:**
- Làm tròn timestamp về giờ để đảm bảo khớp
- Sắp xếp cột theo thứ tự hợp lý cho ML

---

#### `etl/processing/validator.py`

| Thuộc tính | Mô tả |
|------------|-------|
| **Công dụng** | Kiểm tra chất lượng dataset sau khi clean |
| **Trả về** | Báo cáo chi tiết + raise lỗi nếu không đạt ngưỡng |

**Các kiểm tra:**

| Kiểm tra | Mô tả |
|----------|-------|
| `_check_not_empty(df)` | Dataset không rỗng |
| `_check_required_columns(df)` | Đủ cột bắt buộc |
| `_check_villages_coverage(df)` | Đủ 17 làng nghề |
| `_check_record_count_per_village(df)` | Mỗi làng ≥ 1000 records |
| `_check_missing_rates(df)` | Tỷ lệ missing ≤ ngưỡng cho phép (pm25 ≤5%, temperature ≤5%, ...) |
| `_check_time_continuity(df)` | Khoảng cách timestamp ≤ 6 giờ |
| `_check_value_distributions(df)` | Giá trị trong ngưỡng hợp lệ |
| `_check_pm25_pm10_correlation(df)` | Tương quan pm25-pm10 ≥ 0.3 |
| `_check_timestamp_timezone(df)` | Timestamp là UTC-aware |

**Kết quả:** `ValidationResult` dataclass với:
- `passed: bool`
- `errors: List[str]` (lỗi nghiêm trọng → FAIL)
- `warnings: List[str]` (cảnh báo → PASS nhưng cần xem)
- `stats: Dict` (thống kê chi tiết)

---

#### `etl/processing/transformer.py`

> **Lưu ý:** File rỗng (chưa được triển khai)

---

#### `etl/pipeline.py`

> **Lưu ý:** File rỗng (chưa được triển khai)

---

### 3. Scheduler (Lập lịch)

#### `etl/scheduler/jobs.py`

| Thuộc tính | Mô tả |
|------------|-------|
| **Công dụng** | Định nghĩa các job chạy theo lịch |

**Phương thức:**

| Phương thức | Mô tả | Đầu vào | Đầu ra |
|-------------|-------|---------|--------|
| `hourly_update_job()` | Job chạy mỗi giờ: lấy dữ liệu 2 giờ gần nhất, merge, clean, lưu vào DB | Không | Lưu vào bảng `aqi_records` trong PostgreSQL |

**Quy trình:**
1. Lấy dữ liệu 2 giờ gần nhất (overlap để không bỏ sót)
2. Thu thập air quality + weather
3. Merge và clean
4. Lọc chỉ dữ liệu thực (không phải forecast)
5. Lưu vào DB với `if_exists="append"`

---

#### `etl/scheduler/cron.py`

| Thuộc tính | Mô tả |
|------------|-------|
| **Công dụng** | Khởi động APScheduler chạy các job theo lịch |

**Cấu hình:**
- Scheduler: `BlockingScheduler` với timezone `Asia/Ho_Chi_Minh`
- Job: `hourly_update_job` chạy lúc **HH:05** mỗi giờ
- Misyre grace time: 300 giây
- Log: `logs/etl.log`

---

## ML Training (Huấn luyện mô hình)

### 1. Preprocessing (Tiền xử lý)

#### `ml_training/preprocessing/data_loader.py`

| Thuộc tính | Mô tả |
|------------|-------|
| **Công dụng** | Load dữ liệu, encode labels, temporal split, build dataset cho XGBoost và LSTM |

**Các phương thức:**

| Phương thức | Mô tả | Đầu vào | Đầu ra |
|-------------|-------|---------|--------|
| `load_raw_data()` | Load dataset từ parquet | Không | `pd.DataFrame` đã drop cột không cần thiết |
| `encode_labels(df)` | Encode nhãn AQI (Tốt, Trung bình, Kém...) | `df: pd.DataFrame` | `df, LabelEncoder` |
| `temporal_split(df)` | Chia train/val/test theo thời gian (70/15/15) cho mỗi làng | `df: pd.DataFrame` | `train, val, test` DataFrames |
| `clean_after_split(df, features)` | Clean sau khi split (tránh leakage) | `df, features: List[str]` | `pd.DataFrame` đã clean |
| `build_xgb_data(train, val, test)` | Build data cho XGBoost classification | `train, val, test` | `X_train, X_val, X_test, y_train, y_val, y_test` |

**Features cho XGBoost:**
- Pollutants: pm25, pm10, so2, no2, co, o3
- Weather: temperature, humidity, wind_speed, wind_sin, wind_cos, precipitation, pressure, cloud_cover
- Time encoding: hour_sin/cos, month_sin/cos, dow_sin/cos, is_weekend, is_rush_hour
- Lag: pm25_lag1h/3h/6h/12h/24h/48h, aqi_lag1h/3h/6h/12h/24h/48h
- Rolling: pm25_roll3h/6h/24h, aqi_roll3h/6h/24h, pm25_roll24h_std
- Location: village_encoded

**Target:**
- Regression: `aqi_vn` (AQI tổng hợp theo QCVN 05:2023)
- Classification: `aqi_level_encoded` (6 mức: Tốt, Trung bình, Kém (nhạy cảm), Kém, Rất xấu, Nguy hại)

---

#### `ml_training/preprocessing/aqi_calculator.py`

| Thuộc tính | Mô tả |
|------------|-------|
| **Công dụng** | Tính chỉ số AQI theo QCVN 05:2023/BTNMT (Việt Nam) |

**Các phương thức:**

| Phương thức | Mô tả | Đầu vào | Đầu ra |
|-------------|-------|---------|--------|
| `calc_sub_aqi(concentration, pollutant)` | Tính AQI sub-index cho 1 chất ô nhiễm | `concentration: float`, `pollutant: str` | `float` (AQI sub-index) |
| `calc_aqi_row(row)` | Tính AQI tổng hợp = max của các sub-index | `row: pd.Series` | `float` (AQI tổng hợp) |
| `add_aqi_columns(df)` | Thêm các cột AQI vào DataFrame | `df: pd.DataFrame` | `pd.DataFrame` với các cột mới |

**Các cột được thêm:**
- `aqi_vn`: AQI tổng hợp theo QCVN 05:2023
- `aqi_pm25`, `aqi_pm10`, `aqi_so2`, `aqi_no2`, `aqi_co`, `aqi_o3`: Sub-index từng chất
- `aqi_level`: Nhãn chữ (Tốt, Trung bình, Kém (nhạy cảm), Kém, Rất xấu, Nguy hại)
- `aqi_color`: Mã màu hex (#00e400, #ffff00, #ff7e00, #ff0000, #8f3f97, #7e0023)
- `dominant_pollutant`: Chất gây AQI cao nhất

**Bảng ngưỡng AQI theo QCVN 05:2023:**
| AQI | Mức độ | Màu |
|-----|--------|-----|
| 0-50 | Tốt | #00e400 |
| 51-100 | Trung bình | #ffff00 |
| 101-150 | Kém (nhạy cảm) | #ff7e00 |
| 151-200 | Kém | #ff0000 |
| 201-300 | Rất xấu | #8f3f97 |
| 301-500 | Nguy hại | #7e0023 |

---

#### `ml_training/preprocessing/feature_engineer.py`

| Thuộc tính | Mô tả |
|------------|-------|
| **Công dụng** | Tạo dataset hoàn chỉnh cho training: đọc DB, tính AQI, thêm features, xuất file |

**Phương thức:**

| Phương thức | Mô tả | Đầu vào | Đầu ra |
|-------------|-------|---------|--------|
| `build_feature_dataset(target_col)` | Pipeline hoàn chỉnh | `target_col: str` (mặc định "aqi_vn") | `pd.DataFrame` + xuất parquet/csv |

**Quy trình:**
1. Đọc từ PostgreSQL (`aqi_records` table)
2. Tính AQI theo QCVN (gọi `add_aqi_columns`)
3. Thêm time features: hour, day_of_week, month, is_weekend, is_rush_hour, hour_sin/cos, month_sin/cos, dow_sin/cos
4. Encode village → `village_encoded`
5. Thêm lag features: pm25_lag1h/3h/6h/12h/24h/48h, aqi_lag1h/3h/6h/12h/24h/48h
6. Thêm rolling features: pm25_roll3h/6h/24h, aqi_roll3h/6h/24h, pm25_roll24h_std
7. Loại bỏ hàng thiếu target
8. Xuất: `data/exports/ml_dataset.parquet` và `.csv`

---

#### `ml_training/preprocessing/data_splitter_per_village.py`

| Thuộc tính | Mô tả |
|------------|-------|
| **Công dụng** | Chuẩn bị dữ liệu train LSTM riêng cho từng làng nghề (SHAP-guided) |

**Đặc điểm:**
- Áp dụng SHAP-guided feature selection: loại bỏ sub-AQI (aqi_pm25, aqi_o3...) vì gây data leakage
- Loại bỏ village_encoded (train riêng từng làng)
- Giữ: aqi_roll3h (SHAP #1, 32%), o3 (SHAP #2, 17.5%), aqi_lag1h (SHAP #5, 5.9%)

**Output cho mỗi làng:**
```
data/exports/per_village_v2/<village_slug>/
├── train.parquet
├── val.parquet
├── test.parquet
├── scaler_X.pkl
├── scaler_y.pkl
└── meta.json
```

**Features (SHAP-guided):**
- Nhóm 1: Raw pollutants (pm25, o3, so2, no2, pm10, co)
- Nhóm 2: Weather (temperature, humidity, wind_speed, wind_sin, wind_cos, precipitation, pressure, cloud_cover)
- Nhóm 3: Time cyclic (hour_sin/cos, month_sin/cos, dow_sin/cos, is_weekend, is_rush_hour)
- Nhóm 4: Lag AQI (aqi_lag1h/3h/6h/12h/24h/48h)
- Nhóm 5: Lag PM2.5 (pm25_lag1h/3h/6h/12h/24h/48h)
- Nhóm 6: Rolling (aqi_roll3h/6h/24h, pm25_roll3h/6h/24h/24h_std)

---

#### `ml_training/preprocessing/scaler.py`

> **Lưu ý:** File rỗng (chưa được triển khai)

---

### 2. Models (Mô hình)

#### `ml_training/models/xgboost/trainer.py`

| Thuộc tính | Mô tả |
|------------|-------|
| **Công dụng** | Train XGBoost classifier với Optuna hyperparameter tuning + SHAP analysis |
| **Target** | Classification 6 mức AQI |

**Quy trình:**

1. **Load data**: Gọi `data_loader.py`
2. **Class weight**: Compute balanced weights cho imbalanced classes
3. **Baseline**: Train XGBoost baseline (n_estimators=300, max_depth=6)
4. **Optuna tuning**: 30 trials tìm hyperparameters tốt nhất
   - Params: n_estimators, max_depth, learning_rate, subsample, colsample_bytree, min_child_weight, gamma, reg_alpha, reg_lambda
5. **Final model**: Train với best params
6. **Test evaluation**: Accuracy, F1-score, classification report
7. **SHAP analysis**: TreeExplainer + summary plot

**Metrics:**
- Primary: F1-score (weighted)
- Secondary: Accuracy

---

#### `ml_training/models/xgboost/optimizer.py`

> **Lưu ý:** File rỗng (chưa được triển khai - logic đã tích hợp trong trainer.py)

---

#### `ml_training/models/xgboost/evaluator.py`

> **Lưu ý:** File rỗng (chưa được triển khai)

---

#### `ml_training/models/lstm/trainer.py`

| Thuộc tính | Mô tả |
|------------|-------|
| **Công dụng** | Train LSTM + Attention với TensorFlow + Optuna |
| **Framework** | TensorFlow 2.10 + CUDA 11.8 |
| **GPU** | RTX 3050 4GB (optimized) |

**Model architecture:**
```
Input (window, n_features)
→ LSTM(128) + BatchNorm + Dropout
→ LSTM(64) + BatchNorm + Dropout
→ Attention
→ GlobalAveragePooling1D
→ Dense(64, relu) + Dropout
→ Dense(horizon)
```

**Quy trình:**

1. **GPU setup**: TensorFlow memory growth, mixed precision
2. **Load data**: Gọi data_loader (window=48, horizon=6)
3. **Data Generator**: Custom Sequence cho batch training
4. **Model builder**: `build_model(n_features, window, horizon, units_1, units_2, dropout, lr)`
5. **Optuna tuning**: 20 trials với TFKerasPruningCallback
   - Params: units_1, units_2, dropout, lr, batch_size
6. **Final train**: 100 epochs với EarlyStopping, ReduceLROnPlateau, ModelCheckpoint
7. **Save**: Best model → `models/lstm/best.h5`

**Loss**: Huber (robust với outliers)
**Metrics**: MAE

---

#### `ml_training/models/lstm/builder.py`

> **Lưu ý:** File rỗng (chưa được triển khai - logic đã tích hợp trong trainer.py)

---

#### `ml_training/models/lstm/sequence.py`

> **Lưu ý:** File rỗng (chưa được triển khai - logic đã tích hợp trong trainer.py dưới dạng class TimeSeriesGenerator)

---

#### `ml_training/models/lstm/evaluator.py`

> **Lưu ý:** File rỗng (chưa được triển khai)

---

### 3. Evaluation (Đánh giá)

#### `ml_training/evaluation/metrics.py`

| Thuộc tính | Mô tả |
|------------|-------|
| **Công dụng** | Tính các metrics đánh giá mô hình |

**Các metrics:**
- Classification: Accuracy, Precision, Recall, F1-score, Confusion Matrix
- Regression: RMSE, MAE, R², MAPE

---

#### `ml_training/evaluation/plots.py`

| Thuộc tính | Mô tả |
|------------|-------|
| **Công dụng** | Vẽ biểu đồ đánh giá mô hình |

**Các biểu đồ:**
- Actual vs Predicted
- Residual plot
- Feature importance
- Learning curves

---

#### `ml_training/evaluation/shap_analysis.py`

| Thuộc tính | Mô tả |
|------------|-------|
| **Công dụng** | Phân tích SHAP values để hiểu feature importance |

**Phương thức:**
- `compute_shap_values(model, X)`: Tính SHAP values
- `plot_summary(shap_values, X, feature_names)`: Biểu đồ tổng hợp
- `plot_dependence(shap_values, X, feature_name)`: Biểu đồ phụ thuộc

---

## Tổng kết

### Luồng dữ liệu

```
Open-Meteo API
     ↓
[Ingestion] openmeteo_air_fetcher + openmeteo_weather_fetcher
     ↓
[Processing] merger → cleaner → validator
     ↓
PostgreSQL Database
     ↓
[Preprocessing] feature_engineer → data_loader → data_splitter_per_village
     ↓
[ML Training] XGBoost (classification) / LSTM (forecasting)
     ↓
Models: models/xgboost/, models/lstm/
```

### Các file rỗng cần triển khai

| File | Mô tả dự kiến |
|------|---------------|
| `etl/pipeline.py` | Pipeline tổng hợp ETL |
| `etl/processing/transformer.py` | Transform dữ liệu bổ sung |
| `ml_training/preprocessing/scaler.py` | Scaler cho dữ liệu |
| `ml_training/models/xgboost/optimizer.py` | Optimizer riêng |
| `ml_training/models/xgboost/evaluator.py` | Evaluator riêng |
| `ml_training/models/lstm/builder.py` | Model builder riêng |
| `ml_training/models/lstm/sequence.py` | Sequence data generator |
| `ml_training/models/lstm/evaluator.py` | LSTM evaluator |

---

*Document được tạo tự động vào ngày 20/04/2026*