# 📌 AI Air Quality Forecasting — Model Design & Training Guideline

## 🎯 MỤC TIÊU DỰ ÁN

Xây dựng hệ thống AI dự báo **AQI trong tương lai (t + H)**  
→ phục vụ cảnh báo ô nhiễm cho các làng nghề Bắc Ninh.

> ⚠️ Lưu ý quan trọng:
> - KHÔNG dự đoán AQI hiện tại (t)
> - KHÔNG học lại công thức AQI
> - CHỈ dự đoán tương lai: AQI(t + 1 → t + 6)

---

# 🧠 TỔNG QUAN 2 MODEL

## 1️⃣ XGBoost + SHAP (Model phân tích & chọn feature)

Sử dụng:
- :contentReference[oaicite:0]{index=0}
- :contentReference[oaicite:1]{index=1}

### 🎯 Mục đích
KHÔNG phải để dự báo chính

→ Dùng để:
- Hiểu feature nào ảnh hưởng đến AQI
- Phát hiện:
  - ❌ Feature gây leakage
  - ❌ Feature nhiễu
- Chọn ra **feature tốt cho LSTM**

---

### 📥 Input (tại thời điểm t)
pm25(t), pm10(t), o3(t), no2(t)
temperature(t), humidity(t), wind_speed(t)
aqi_lag1h(t), aqi_roll3h(t)
hour_sin(t), hour_cos(t)

---

### 📤 Target (BẮT BUỘC)
AQI(t + H)

Ví dụ:
H = 6 → predict AQI sau 6 giờ


---

### ❌ KHÔNG ĐƯỢC dùng
- aqi_pm25, aqi_o3,... (sub-AQI) → leakage
- aqi hiện tại nếu predict chính nó
- feature chứa thông tin tương lai

---

### 📊 Output của XGBoost
- R², MAE (chỉ để tham khảo)
- Feature importance từ SHAP

---

### ⚠️ Cảnh báo quan trọng

| Hiện tượng | Nguyên nhân |
|----------|------------|
| R² ≈ 1.0 | Data leakage |
| Model quá tốt | Feature chứa target |
| SHAP chọn lag/rolling quá cao | Có thể leak |

---

---

## 2️⃣ LSTM (Model dự báo chính)

Sử dụng:
- :contentReference[oaicite:2]{index=2}

---

### 🎯 Mục đích
Dự báo chuỗi thời gian:

AQI(t + 1 → t + H)

---

### 📥 Input
Chuỗi dữ liệu quá khứ:

X = [t-WINDOW ... t]

Ví dụ:
WINDOW = 48 giờ

---

### 📤 Output
y = [AQI(t+1), AQI(t+2), ..., AQI(t+H)]

---

### 📌 Feature sử dụng

👉 KHÔNG phải chỉ lấy top 5 từ SHAP

👉 Mà:
Feature tốt = Feature hợp lý + không leakage

Ví dụ bộ feature chuẩn:
pm25, pm10, o3, no2
temperature, humidity, wind_speed
aqi_lag1h, aqi_lag3h
aqi_roll3h, aqi_roll6h
hour_sin, hour_cos

---

# 🔄 PIPELINE CHUẨN

## Bước 1 — Data Collection
- Air quality
- Weather

---

## Bước 2 — Feature Engineering

### Tạo:
- Lag:
aqi_lag1h = AQI(t-1)

- Rolling:

aqi_roll3h = mean(t-2, t-1, t)

---

### ⚠️ NGUYÊN TẮC QUAN TRỌNG

> ❌ KHÔNG dùng future

Sai:

mean(t, t+1, t+2)


Đúng:

mean(t-2, t-1, t)


---

## Bước 3 — Label Creation


target = AQI(t + H)


Ví dụ:

H = 6


---

## Bước 4 — Time Series Split


Train: 70% (quá khứ)
Val: 15%
Test: 15% (tương lai)


❌ KHÔNG dùng random split

---

## Bước 5 — Train XGBoost + SHAP

→ Mục tiêu:
- kiểm tra pipeline
- chọn feature

---

## Bước 6 — Chọn Feature

### ❌ Sai:

chỉ lấy top 5 SHAP


### ✅ Đúng:
bỏ feature leakage
bỏ feature vô nghĩa
giữ feature có ý nghĩa vật lý

---

## Bước 7 — Train LSTM

→ dùng:
- dữ liệu chuỗi
- feature đã lọc

---

# 🚨 DATA LEAKAGE — NGUY HIỂM NHẤT

## Ví dụ leakage

| Feature | Lý do |
|--------|------|
| aqi_pm25 | chứa thông tin target |
| aqi_roll3h (sai cách tính) | dùng future |
| AQI(t) khi predict AQI(t) | trivial |

---

## Dấu hiệu nhận biết

- R² > 0.95 bất thường
- Model học cực nhanh
- Validation ≈ Train

---

---

# 🎯 KẾT LUẬN

## Vai trò từng model

### XGBoost + SHAP
→ “Hiểu dữ liệu”
- Feature nào quan trọng
- Có leakage không

---

### LSTM
→ “Dự báo tương lai”
- AQI(t+H)

---

## Nguyên tắc vàng

> ✅ Model phải dự đoán tương lai  
> ❌ Không được nhìn thấy tương lai  

---

# 🔥 CHECKLIST TRƯỚC KHI TRAIN

- [ ] Target là AQI(t+H)
- [ ] Không có feature từ future
- [ ] Lag / rolling đúng chiều thời gian
- [ ] Split theo time
- [ ] Không dùng sub-AQI
- [ ] R² không quá bất thường

---

# 📌 GHI NHỚ QUAN TRỌNG

> XGBoost không phải model chính  
> SHAP không phải để chọn top N feature  
> LSTM mới là model dự báo chính  

---