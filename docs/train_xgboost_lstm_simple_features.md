# Hướng dẫn Train XGBoost + SHAP và LSTM với Features Cơ bản

## Mục lục

1. [Tổng quan](#tổng-quan)
2. [Cấu hình Features](#cấu-hình-features)
3. [Pipeline XGBoost + SHAP](#pipeline-xgboost--shap)
4. [Pipeline LSTM](#pipeline-lstm)
5. [Chạy Training](#chạy-training)

---

## 1. Tổng quan

### Features cho dự báo & cảnh báo (theo yêu cầu)

| Nhóm | Features |
|------|----------|
| **Pollutants** | `pm25`, `pm10`, `so2`, `no2`, `co`, `o3` |
| **Weather** | `temperature`, `humidity`, `wind_speed`, `wind_sin`, `wind_cos`, `precipitation`, `pressure`, `cloud_cover` |
| **Time** | `hour_sin`, `hour_cos` |

**Tổng: 16 features**

### Không sử dụng (tránh leakage)

- ❌ Sub-AQI: `aqi_pm25`, `aqi_pm10`, `aqi_so2`, `aqi_no2`, `aqi_co`, `aqi_o3`
- ❌ Lag: `pm25_lag*`, `aqi_lag*`
- ❌ Rolling: `pm25_roll*`, `aqi_roll*`
- ❌ `month`, `dow`, `is_weekend`, `is_rush_hour`

---

## 2. Cấu hình Features (16 features)

### Bước 1: Cập nhật `data_loader.py`

```python
# filepath: ml_training/preprocessing/data_loader.py

# 16 features (theo yêu cầu)
BASE_FEATURES = [
    # Pollutants (6)
    "pm25", "pm10", "so2", "no2", "co", "o3",

    # Weather (8)
    "temperature", "humidity", "wind_speed",
    "wind_sin", "wind_cos",
    "precipitation", "pressure", "cloud_cover",

    # Time (2)
    "hour_sin", "hour_cos",
]

# Target
TARGET_REGRESSION = "aqi_vn"
TARGET_CLASSIFICATION = "aqi_level_encoded"
```

### Bước 2: Kiểm tra dataset

```python
required_cols = BASE_FEATURES + ["aqi_vn", "aqi_level_encoded"]
missing = [c for c in required_cols if c not in df.columns]
if missing:
    raise ValueError(f"Thiếu cột: {missing}")
```

---

## 3. Pipeline XGBoost + SHAP

### 3.1 Luồng training

```
Dataset (22 features)
       ↓
Temporal Split (70/15/15)
       ↓
Build XGBoost data
       ↓
Class Weight (imbalanced)
       ↓
Baseline Model (n_estimators=300)
       ↓
Optuna Tuning (30 trials)
       ↓
Best Model + SHAP Analysis
       ↓
Export: models/xgboost/best_model.json
```

### 3.2 Cấu hình hyperparameters

```python
# filepath: ml_training/models/xgboost/trainer.py

# 16 features
XGB_FEATURES = [
    # Pollutants (6)
    "pm25", "pm10", "so2", "no2", "co", "o3",
    # Weather (8)
    "temperature", "humidity", "wind_speed",
    "wind_sin", "wind_cos",
    "precipitation", "pressure", "cloud_cover",
    # Time (2)
    "hour_sin", "hour_cos",
]

TARGET = "aqi_level_encoded"  # Classification 6 mức
```

### 3.3 Optuna objective

```python
# filepath: ml_training/models/xgboost/trainer.py

def objective(trial):
    params = {
        "n_estimators": trial.suggest_int("n_estimators", 200, 800),
        "max_depth": trial.suggest_int("max_depth", 4, 10),
        "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.2, log=True),
        "subsample": trial.suggest_float("subsample", 0.6, 1.0),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.6, 1.0),
        "min_child_weight": trial.suggest_int("min_child_weight", 1, 10),
        "gamma": trial.suggest_float("gamma", 0, 5),
        "reg_alpha": trial.suggest_float("reg_alpha", 0, 1),
        "reg_lambda": trial.suggest_float("reg_lambda", 0.5, 5),
    }

    model = xgb.XGBClassifier(
        **params,
        eval_metric="mlogloss",
        random_state=SEED,
        n_jobs=-1,
    )

    model.fit(
        X_tr, y_tr,
        sample_weight=sample_weights,
        eval_set=[(X_vl, y_vl)],
        early_stopping_rounds=30,
        verbose=False
    )

    y_pred = model.predict(X_vl)
    return f1_score(y_vl, y_pred, average="weighted")
```

### 3.4 SHAP Analysis

```python
# filepath: ml_training/models/xgboost/trainer.py

print("\n[3/3] SHAP Analysis...")

explainer = shap.TreeExplainer(best_model)
shap_values = explainer.shap_values(X_te)

# Summary plot
plt.figure(figsize=(12, 8))
shap.summary_plot(shap_values, X_te, feature_names=XGB_FEATURES, show=False)
plt.tight_layout()
plt.savefig(f"{MODEL_DIR}/shap_summary.png", dpi=150)
plt.close()

# Feature importance
plt.figure(figsize=(10, 6))
shap.summary_plot(shap_values, X_te, feature_names=XGB_FEATURES, plot_type="bar", show=False)
plt.tight_layout()
plt.savefig(f"{MODEL_DIR}/shap_importance.png", dpi=150)
plt.close()

print(f"✓ SHAP plots saved to {MODEL_DIR}")
```

---

## 4. Pipeline LSTM

### 4.1 Luồng training

```
Dataset (22 features)
       ↓
Temporal Split per Village
       ↓
Build Sequences (window=48, horizon=6)
       ↓
MinMaxScaler (fit on train only)
       ↓
Build LSTM data
       ↓
Model: LSTM(128) → LSTM(64) → Attention → Dense
       ↓
Optuna Tuning (20 trials)
       ↓
Best Model + Evaluation
       ↓
Export: models/lstm/best.h5
```

### 4.2 Cấu hình Features

```python
# filepath: ml_training/models/lstm/trainer.py

# 16 features
LSTM_FEATURES = [
    # Pollutants (6)
    "pm25", "pm10", "so2", "no2", "co", "o3",
    # Weather (8)
    "temperature", "humidity", "wind_speed",
    "wind_sin", "wind_cos",
    "precipitation", "pressure", "cloud_cover",
    # Time (2)
    "hour_sin", "hour_cos",
]

WINDOW = 48    # 48 giờ quá khứ
HORIZON = 6    # Dự báo 6 giờ tới
```

### 4.3 Model Architecture

```python
# filepath: ml_training/models/lstm/trainer.py

def build_model(n_features, window, horizon,
                units_1=128, units_2=64,
                dropout=0.2, lr=5e-4):

    inputs = Input(shape=(window, n_features))

    # LSTM Layer 1
    x = LSTM(units_1, return_sequences=True)(inputs)
    x = BatchNormalization()(x)
    x = Dropout(dropout)(x)

    # LSTM Layer 2 + Attention
    x = LSTM(units_2, return_sequences=True)(x)
    attention = Attention()([x, x])
    x = GlobalAveragePooling1D()(attention)

    # Dense layers
    x = Dense(64, activation="relu")(x)
    x = Dropout(dropout)(x)
    outputs = Dense(horizon)(x)

    model = Model(inputs, outputs)
    model.compile(
        optimizer=Adam(learning_rate=lr),
        loss="huber",
        metrics=["mae"]
    )

    return model
```

### 4.4 Optuna Objective

```python
# filepath: ml_training/models/lstm/trainer.py

def objective(trial):
    units_1 = trial.suggest_int("units_1", 64, 256)
    units_2 = trial.suggest_int("units_2", 32, 128)
    dropout = trial.suggest_float("dropout", 0.1, 0.4)
    lr = trial.suggest_float("lr", 1e-5, 1e-3, log=True)
    batch_size = trial.suggest_int("batch_size", 16, 64)

    model = build_model(
        N_FEATURES, WINDOW, HORIZON,
        units_1, units_2, dropout, lr
    )

    history = model.fit(
        train_gen,
        validation_data=val_gen,
        epochs=30,
        callbacks=[
            EarlyStopping(patience=5, restore_best_weights=True),
            TFKerasPruningCallback(trial, "val_mae")
        ],
        verbose=False
    )

    val_mae = min(history.history["val_mae"])
    return val_mae
```

---

## 5. Chạy Training

### 5.1 Chuẩn bị môi trường

```bash
# Activate virtual environment
cd c:\Users\Acer\Desktop\DATN\DATN_AIR_GROARD_BN_2026
.venv\Scripts\activate

# Verify packages
pip list | grep -E "xgboost|shap|tensorflow|optuna"
```

### 5.2 Chạy XGBoost + SHAP

```bash
# Method 1: Direct run
python ml_training/models/xgboost/trainer.py

# Method 2: Via script
python scripts/train_model.py --model xgboost
```

**Output:**
```
🚀 PIPELINE XGBOOST + SHAP (PRODUCTION)
📥 Loading dataset...
⚖️ Class weights: ...
[1/3] Baseline model...
Baseline F1: 0.7234
[2/3] Optuna tuning...
Best trial: 15 - F1: 0.7892
[3/3] SHAP Analysis...
✓ SHAP plots saved to models/xgboost/
```

### 5.3 Chạy LSTM

```bash
# Method 1: Direct run
python ml_training/models/lstm/trainer.py

# Method 2: Via script
python scripts/train_model.py --model lstm
```

**Output:**
```
🚀 PIPELINE LSTM + ATTENTION
✓ TensorFlow: 2.15.0
✓ GPU: NVIDIA GeForce RTX 3050
📥 Loading dataset...
[1/3] Building sequences...
[2/3] Optuna tuning...
Best trial: 8 - Val MAE: 12.34
[3/3] Training final model...
✓ Model saved to models/lstm/best.h5
```

### 5.4 Kiểm tra kết quả

```bash
# XGBoost outputs
ls models/xgboost/
# → best_model.json  shap_summary.png  shap_importance.png

# LSTM outputs
ls models/lstm/
# → best.h5  scaler_X.pkl  scaler_y.pkl
```

---

## 6. So sánh 2 Models

| Khía cạnh | XGBoost + SHAP | LSTM |
|-----------|----------------|------|
| **Task** | Classification (6 mức AQI) | Regression (dự báo AQI) |
| **Input** | 16 features (1 timestep) | 16 features × 48 timesteps |
| **Output** | 1 label (Tốt/Trung bình/Kém...) | 6 giá trị AQI tương lai |
| **Features** | 16 | 16 |
| **Use case** | Cảnh báo mức độ hiện tại | Dự báo AQI 6 giờ tới |

### Khi nào dùng model nào?

- **XGBoost**: Cảnh báo AQI hiện tại → "AQI hiện tại: Kém (nhạy cảm)"
- **LSTM**: Dự báo AQI tương lai → "AQI dự báo 6h tới: 85 (Trung bình)"

---

## 7. Tóm tắt

### 16 Features (theo yêu cầu)

| # | Feature | Nhóm |
|---|---------|------|
| 1-6 | `pm25`, `pm10`, `so2`, `no2`, `co`, `o3` | Pollutants |
| 7-14 | `temperature`, `humidity`, `wind_speed`, `wind_sin`, `wind_cos`, `precipitation`, `pressure`, `cloud_cover` | Weather |
| 15-16 | `hour_sin`, `hour_cos` | Time |

### Luồng training

```
Dataset (16 features)
       ↓
XGBoost → Classification (cảnh báo mức AQI)
       ↓
LSTM → Forecasting (dự báo AQI tương lai)
```

---

*Document created: 21/04/2026*