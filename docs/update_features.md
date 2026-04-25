# 🔧 Hướng dẫn Feature Reduction & Retrain XGBoost + LSTM
## AirGuard BN — Tối ưu Pipeline dự báo AQI

---

## Tổng quan thay đổi

| Hạng mục | Trước | Sau |
|---|---|---|
| Số features XGBoost | 61 features | ~20 features (top SHAP) |
| Số features LSTM | 37 features (v2) | **12 features** (reduced) |
| Sub-AQI features | Có (leakage) | Loại bỏ hoàn toàn |
| Lag xa (24h, 48h) | Có | Loại bỏ |
| Rolling dài (24h) | Có | Loại bỏ |
| Features thời tiết phụ | Có | Loại bỏ |

---

## Phần 1 — Feature Set cuối cùng

### 1.1 LSTM features (12 features — recommended)

```python
LSTM_FEATURES_REDUCED = [

    # === (A) Chất ô nhiễm gốc ===
    # Giữ 4 chất chính — bỏ co vì ít ảnh hưởng theo SHAP
    "pm25",    # PM2.5 — chỉ số trung tâm của AQI
    "pm10",    # PM10 — liên quan PM2.5
    "o3",      # Ozone — SHAP rank 2 (0.175)
    "no2",     # NO2 — đặc trưng làng nghề đốt nhiên liệu

    # === (B) Temporal lag — QUAN TRỌNG NHẤT ===
    # Chỉ giữ lag ngắn — lag xa (24h, 48h) thêm nhiễu
    "aqi_lag1h",    # SHAP rank 5 (0.059) — 1 giờ trước
    "aqi_lag3h",    # SHAP rank 12 (0.009) — 3 giờ trước

    # === (C) Rolling mean — signal mượt ===
    "aqi_roll3h",   # SHAP rank 1 (0.320) — QUAN TRỌNG NHẤT
    "aqi_roll6h",   # SHAP rank 7 (0.033) — xu hướng 6h

    # === (D) Thời tiết tối thiểu ===
    # Chỉ 3 biến thời tiết có ảnh hưởng vật lý rõ ràng
    "temperature",  # nhiệt độ — ảnh hưởng phát tán ô nhiễm
    "humidity",     # độ ẩm — PM2.5 tăng khi ẩm cao
    "wind_speed",   # tốc độ gió — phát tán ô nhiễm

    # === (E) Time encoding tuần hoàn ===
    "hour_sin",     # SHAP rank 15 (0.007) — pattern theo giờ
    "hour_cos",     # cặp với hour_sin
]
# Tổng: 12 features
```

### 1.2 XGBoost features (giữ đầy đủ để SHAP có đủ thông tin)

XGBoost **không cần giảm features** — tree model tự lọc features không quan trọng qua splitting. Giảm features XGBoost sẽ làm mất thông tin cho SHAP analysis.

```python
# Giữ nguyên XGB_FEATURES đầy đủ cho XGBoost
# Chỉ LOẠI sub-AQI nếu muốn tránh leakage hoàn toàn
XGB_FEATURES_CLEAN = [
    # Raw pollutants
    "pm25", "pm10", "o3", "no2", "so2", "co",
    # Weather
    "temperature", "humidity", "wind_speed", "wind_sin", "wind_cos",
    "precipitation", "pressure", "cloud_cover",
    # Time
    "hour_sin", "hour_cos", "month_sin", "month_cos",
    "dow_sin", "dow_cos", "is_weekend", "is_rush_hour",
    # Lag AQI
    "aqi_lag1h", "aqi_lag3h", "aqi_lag6h",
    "aqi_lag12h", "aqi_lag24h", "aqi_lag48h",
    # Lag PM2.5
    "pm25_lag1h", "pm25_lag3h", "pm25_lag6h",
    "pm25_lag12h", "pm25_lag24h", "pm25_lag48h",
    # Rolling
    "aqi_roll3h", "aqi_roll6h", "aqi_roll24h",
    "pm25_roll3h", "pm25_roll6h", "pm25_roll24h",
    "pm25_roll24h_std",
    # KHÔNG có: aqi_pm25, aqi_o3, aqi_pm10, aqi_no2, aqi_so2 (leakage)
    # KHÔNG có: village_encoded (xử lý theo làng riêng)
]
```

### 1.3 Bảng quyết định loại bỏ

| Feature | Lý do loại bỏ |
|---|---|
| `aqi_pm25`, `aqi_o3`, `aqi_pm10`, `aqi_no2`, `aqi_so2` | **Data leakage** — tính từ chính PM2.5, O3... LSTM học shortcut |
| `aqi_lag6h`, `aqi_lag12h`, `aqi_lag24h`, `aqi_lag48h` | Lag xa → nhiễu, Attention đã học được context dài |
| `pm25_lag1h` → `pm25_lag48h` | Trùng thông tin với `aqi_lag*` và `aqi_roll*` |
| `aqi_roll24h`, `pm25_roll*` | Rolling dài → chậm phản ứng, trùng với `aqi_roll3h` |
| `so2`, `co` | SHAP thấp (<0.01), ít đặc trưng so với pm25/o3 |
| `wind_sin`, `wind_cos` | Đã có `wind_speed` — hướng gió ít ảnh hưởng hơn tốc độ |
| `precipitation`, `pressure`, `cloud_cover` | SHAP thấp, ít tác động ngắn hạn |
| `month_sin`, `month_cos`, `dow_sin`, `dow_cos` | Ít biến động trong window 48h |
| `is_weekend`, `is_rush_hour` | Dữ liệu làng nghề không nghỉ cuối tuần |
| `village_encoded` | Train riêng từng làng — không cần |

---

## Phần 2 — Thay đổi file code

### 2.1 Sửa `data_splitter_per_village.py`

Mở file `ml_training/preprocessing/data_splitter_per_village.py` (bản v2),
tìm và thay thế toàn bộ khối `FEATURE_COLS`:

```python
# ── THAY THẾ FEATURE_COLS bằng version reduced ──────────────────────────────
FEATURE_COLS = [
    # (A) Chất ô nhiễm gốc
    "pm25", "pm10", "o3", "no2",

    # (B) Temporal lag ngắn
    "aqi_lag1h", "aqi_lag3h",

    # (C) Rolling mean
    "aqi_roll3h", "aqi_roll6h",

    # (D) Thời tiết tối thiểu
    "temperature", "humidity", "wind_speed",

    # (E) Time encoding
    "hour_sin", "hour_cos",
]

TARGET_COL  = "aqi_vn"
OUTPUT_DIR  = "../data/exports/per_village_v3"   # ← đổi tên để không ghi đè v2
```

Đổi tên `OUTPUT_DIR` thành `per_village_v3` để giữ lại kết quả v2 để so sánh.

---

### 2.2 Sửa notebook `04_lstm_per_village_v2.ipynb` — Cell 3 (Cấu hình)

Tìm phần khai báo đường dẫn trong Cell 2 (Mount Drive), thay đổi:

```python
# Đổi từ v2 sang v3
PER_VLG_DIR = f'{BASE_DIR}/data/per_village_v3'      # ← v3
MODELS_DIR  = f'{BASE_DIR}/models/per_village_v3'    # ← v3
PLOTS_DIR   = f'{BASE_DIR}/plots/per_village_v3'     # ← v3
```

---

### 2.3 Sửa `data_splitter.py` (cho XGBoost)

Mở `ml_training/preprocessing/data_splitter.py`, sửa `XGB_FEATURES`:

```python
# XGBoost giữ nhiều features hơn để SHAP phân tích đầy đủ
# Chỉ loại sub-AQI (leakage) và village_encoded
XGB_FEATURES = [
    "pm25", "pm10", "o3", "no2", "so2", "co",
    "temperature", "humidity", "wind_speed",
    "wind_sin", "wind_cos",
    "precipitation", "pressure", "cloud_cover",
    "hour_sin", "hour_cos",
    "month_sin", "month_cos",
    "dow_sin", "dow_cos",
    "is_weekend", "is_rush_hour",
    "aqi_lag1h", "aqi_lag3h", "aqi_lag6h",
    "aqi_lag12h", "aqi_lag24h", "aqi_lag48h",
    "pm25_lag1h", "pm25_lag3h", "pm25_lag6h",
    "pm25_lag12h", "pm25_lag24h", "pm25_lag48h",
    "aqi_roll3h", "aqi_roll6h", "aqi_roll24h",
    "pm25_roll3h", "pm25_roll6h", "pm25_roll24h",
    "pm25_roll24h_std",
    # KHÔNG có: aqi_pm25, aqi_o3, aqi_pm10, aqi_no2, aqi_so2
    # KHÔNG có: village_encoded
]
```

---

## Phần 3 — Thứ tự thực hiện

### Bước 1 — Tạo dataset v3

```cmd
cd DATN_AIR_GROARD_BN_2026\ml_training\preprocessing

REM Chạy script đã sửa OUTPUT_DIR = per_village_v3
python data_splitter_per_village.py
```

Kiểm tra output:

```
Phong Khê        32,201 records  → train=22,540  val=4,830  test=4,831  ✓
Đa Hội           32,201 records  → ...
...
```

Số features phải là **12** thay vì 37.

---

### Bước 2 — Nén và upload lên Colab

```cmd
powershell Compress-Archive `
    data\exports\per_village_v3 `
    per_village_v3.zip
```

Upload `per_village_v3.zip` lên `Google Drive/AirGuard_BN/data/`.

---

### Bước 3 — Retrain XGBoost (nếu cần)

Mở `ml_training/notebooks/02_xgboost.ipynb`, chạy lại với `XGB_FEATURES` mới.
Kết quả SHAP mới sẽ xác nhận 12 features đã chọn có đủ signal không.

```python
# Trong notebook XGBoost, thêm cell so sánh feature importance:
fi_new = pd.DataFrame({
    'feature':    feat_names,
    'importance': best_model.feature_importances_
}).sort_values('importance', ascending=False)

print("Top 15 features sau khi loại leakage:")
print(fi_new.head(15).to_string(index=False))
```

---

### Bước 4 — Retrain LSTM trên Colab

Mở notebook `04_lstm_per_village_v2.ipynb`, sửa đường dẫn sang v3 (Phần 2.2),
rồi chạy tuần tự từ Cell 1.

---

### Bước 5 — So sánh 3 phiên bản

Sau khi có kết quả v3, chạy cell so sánh trong notebook:

```python
# Cell so sánh — điền R² của từng phiên bản
comparison = {
    'village': [...],             # danh sách làng
    'v1_full_leakage': [...],     # R² v1 (61 features, có leakage)
    'v2_no_leakage':   [...],     # R² v2 (37 features, no leakage)
    'v3_reduced':      [...],     # R² v3 (12 features, reduced)
}

import pandas as pd
df_cmp = pd.DataFrame(comparison)
print(df_cmp.to_string(index=False))

# Vẽ grouped bar chart
import matplotlib.pyplot as plt
import numpy as np

x     = np.arange(len(comparison['village']))
w     = 0.25
fig, ax = plt.subplots(figsize=(16, 6))

ax.bar(x - w,   comparison['v1_full_leakage'], w, label='v1 full+leakage',
       color='#e74c3c', alpha=0.8)
ax.bar(x,       comparison['v2_no_leakage'],   w, label='v2 no leakage (37f)',
       color='#f39c12', alpha=0.8)
ax.bar(x + w,   comparison['v3_reduced'],       w, label='v3 reduced (12f)',
       color='#2ecc71', alpha=0.8)

ax.axhline(0.85, color='green', ls='--', lw=1.5, label='Target 0.85')
ax.set_xticks(x)
ax.set_xticklabels(comparison['village'], rotation=25, ha='right')
ax.set_ylabel('R²')
ax.set_title('So sánh R² — v1 vs v2 vs v3')
ax.legend()
ax.grid(True, alpha=0.3, axis='y')
plt.tight_layout()
plt.show()
```

---

## Phần 4 — Kết quả kỳ vọng

### Lý do v3 (12 features) có thể tốt hơn v2 (37 features)

**1. Giảm curse of dimensionality:** LSTM với 12 features cần ít parameters hơn
→ ít overfitting hơn, generalize tốt hơn với dataset ~32K records/làng.

**2. Loại nhiễu:** 25 features bị loại đều có SHAP thấp (<0.005)
→ chúng chỉ thêm nhiễu vào gradient descent mà không cải thiện R².

**3. Training nhanh hơn:** 12 features vs 37 features → sequences nhỏ hơn
→ mỗi trial Optuna nhanh hơn → có thể tăng `N_TRIALS` từ 25 lên 40.

**4. `aqi_roll3h` là signal mạnh nhất (SHAP 32%):** Giữ feature này là đủ
để LSTM capture được momentum ô nhiễm ngắn hạn.

| Metric | v1 (61f, leakage) | v2 (37f, sạch) | v3 (12f, reduced) |
|---|---|---|---|
| R² tổng (kỳ vọng) | ~0.37 giả tạo | ~0.70–0.80 | **~0.80–0.90** |
| h+1 R² | ~0.79 | ~0.85 | **~0.88–0.92** |
| h+6 R² | ~0.18 | ~0.60 | **~0.65–0.75** |
| Training time/làng | ~8 phút | ~5 phút | **~3 phút** |
| Overfitting risk | Cao | Trung bình | **Thấp** |

---

## Phần 5 — Điều chỉnh Hyperparameter cho 12 features

Vì input nhỏ hơn (12 features thay vì 37), điều chỉnh search space trong Optuna:

```python
# Trong hàm objective() của notebook — Cell 6
def objective(trial):
    # Giảm units vì input nhỏ hơn
    units_1 = trial.suggest_categorical('units_1', [32, 64, 128])   # bỏ 256
    units_2 = trial.suggest_categorical('units_2', [16, 32, 64])    # bỏ 128
    dropout = trial.suggest_float('dropout', 0.1, 0.35)
    lr      = trial.suggest_float('lr', 5e-4, 1e-2, log=True)       # lr cao hơn
    batch   = trial.suggest_categorical('batch_size', [128, 256, 512]) # tăng batch

    # Với 12 features, batch lớn hơn giúp gradient ổn định hơn
    ...
```

Và tăng số trials vì mỗi trial nhanh hơn:

```python
N_TRIALS   = 40    # tăng từ 25 → 40
MAX_EPOCHS = 120   # tăng từ 100 → 120 vì model nhỏ hơn, cần nhiều epoch hơn
```

---

## Phần 6 — Checklist trước khi train

```
□ data_splitter_per_village.py đã sửa FEATURE_COLS = 12 features
□ OUTPUT_DIR = "../data/exports/per_village_v3"
□ Chạy script → kiểm tra n_features = 12 trong meta.json
□ Nén per_village_v3.zip → upload lên Drive
□ Notebook Cell 2: PER_VLG_DIR trỏ đúng per_village_v3
□ Notebook Cell 2: MODELS_DIR trỏ đúng per_village_v3
□ Notebook Cell 3: N_TRIALS = 40, MAX_EPOCHS = 120
□ Notebook Cell 6: search space Optuna đã điều chỉnh
□ Bật GPU T4 trên Colab
□ Chạy tuần tự Cell 1 → Cell 12
```

---

## Phần 7 — Xử lý nếu v3 kém hơn v2

Nếu R² của v3 thấp hơn v2, thêm dần features theo thứ tự ưu tiên:

```
Thử thêm:
  1. "aqi_lag6h"      → lag 6h thêm context
  2. "pm25_roll3h"    → rolling PM2.5 (SHAP rank 14)
  3. "so2"            → đặc trưng làng nghề đốt than
  4. "wind_sin", "wind_cos"  → nếu hướng gió quan trọng

Không thêm lại:
  ✗ aqi_lag24h, aqi_lag48h  → nhiễu
  ✗ aqi_pm25, aqi_o3...     → leakage
  ✗ cloud_cover, pressure   → SHAP = 0
```

Công thức thực nghiệm: nếu thêm feature mà **val R² tăng ≥ 0.01** → giữ,
nếu không → loại bỏ.

---

## Tóm tắt nhanh

```
1. Sửa FEATURE_COLS → 12 features, OUTPUT_DIR → per_village_v3
2. python data_splitter_per_village.py
3. Upload per_village_v3.zip lên Drive
4. Sửa đường dẫn notebook → v3, N_TRIALS=40
5. Chạy notebook trên Colab T4
6. So sánh R² v1/v2/v3 → chọn version tốt nhất cho backend
```