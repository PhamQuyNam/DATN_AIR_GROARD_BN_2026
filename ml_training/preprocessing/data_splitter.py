"""
ml_training/preprocessing/data_splitter.py

Pipeline chuẩn production:
- Load & clean data
- Temporal split theo từng village (NO leakage)
- Build dataset cho:
    + XGBoost (classification)
    + LSTM (time-series forecasting)
"""

import os
import numpy as np
import pandas as pd
import joblib
from typing import Tuple, List
from sklearn.preprocessing import MinMaxScaler, LabelEncoder


# ─────────────────────────────────────────────────────────────
# PATH CONFIG
# ─────────────────────────────────────────────────────────────
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH  = os.path.join(BASE_DIR, "../data/exports/ml_dataset.parquet")
EXPORT_DIR    = os.path.join(BASE_DIR, "../data/exports")

os.makedirs(EXPORT_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────
# TARGET CONFIG
# ─────────────────────────────────────────────────────────────
TARGET_REGRESSION      = "aqi_vn"
TARGET_CLASSIFICATION  = "aqi_level_encoded"

LABEL_ORDER = [
    "Tốt", "Trung bình", "Kém (nhạy cảm)",
    "Kém", "Rất xấu", "Nguy hại"
]


# ─────────────────────────────────────────────────────────────
# FEATURE CONFIG — v3 (theo update_features.md)
# ══════════════════════════════════════════════════════════════
BASE_FEATURES = [
    # Pollutants (6)
    "pm25", "pm10", "so2", "no2", "co", "o3",

    # Weather (8)
    "temperature", "humidity", "wind_speed",
    "wind_sin", "wind_cos",
    "precipitation", "pressure", "cloud_cover",

    # Time encoding (8)
    "hour_sin", "hour_cos",
    "month_sin", "month_cos",
    "dow_sin", "dow_cos",
    "is_weekend", "is_rush_hour",

    # Lag AQI (6)
    "aqi_lag1h", "aqi_lag3h", "aqi_lag6h",
    "aqi_lag12h", "aqi_lag24h", "aqi_lag48h",

    # Lag PM2.5 (6)
    "pm25_lag1h", "pm25_lag3h", "pm25_lag6h",
    "pm25_lag12h", "pm25_lag24h", "pm25_lag48h",

    # Rolling (7)
    "aqi_roll3h", "aqi_roll6h", "aqi_roll24h",
    "pm25_roll3h", "pm25_roll6h", "pm25_roll24h",
    "pm25_roll24h_std",
]

# XGBoost: giữ đầy đủ features để SHAP analysis
# Chỉ LOẠI: sub-AQI (leakage), village_encoded
XGB_FEATURES = BASE_FEATURES  # 41 features, không có leakage

# LSTM: dùng 12 features (reduced)
LSTM_FEATURES = [
    # Pollutants (4)
    "pm25", "pm10", "o3", "no2",
    # Lag ngắn (2)
    "aqi_lag1h", "aqi_lag3h",
    # Rolling (2)
    "aqi_roll3h", "aqi_roll6h",
    # Weather (3)
    "temperature", "humidity", "wind_speed",
    # Time (1)
    "hour_sin", "hour_cos",
]  # 12 features


# ─────────────────────────────────────────────────────────────
# STEP 1 — LOAD & BASIC CLEAN
# ─────────────────────────────────────────────────────────────
def load_raw_data() -> pd.DataFrame:
    print("📥 Loading dataset...")
    df = pd.read_parquet(DATASET_PATH)

    # Drop irrelevant columns
    drop_cols = [
        "source", "aqi_color", "dominant_pollutant",
        "is_forecast", "dust", "aod",
        "lat", "lon", "pm25_category"
    ]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns])

    # Timestamp
    df["timestamp"] = pd.to_datetime(df["timestamp"])

    return df


# ─────────────────────────────────────────────────────────────
# STEP 2 — LABEL ENCODING
# ─────────────────────────────────────────────────────────────
def encode_labels(df: pd.DataFrame) -> Tuple[pd.DataFrame, LabelEncoder]:
    print("🏷️ Encoding labels...")

    le = LabelEncoder()
    le.fit(LABEL_ORDER)

    df["aqi_level"] = df["aqi_level"].fillna("Trung bình")
    df["aqi_level_encoded"] = le.transform(df["aqi_level"])

    joblib.dump(le, f"{EXPORT_DIR}/label_encoder.pkl")

    return df, le


# ─────────────────────────────────────────────────────────────
# STEP 3 — TEMPORAL SPLIT (NO LEAKAGE)
# ─────────────────────────────────────────────────────────────
def temporal_split(df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    print("⏳ Temporal split by village...")

    trains, vals, tests = [], [], []

    for village, group in df.groupby("village"):
        group = group.sort_values("timestamp")

        n = len(group)
        i_train = int(n * 0.7)
        i_val   = int(n * 0.85)

        trains.append(group.iloc[:i_train])
        vals.append(group.iloc[i_train:i_val])
        tests.append(group.iloc[i_val:])

    train = pd.concat(trains).reset_index(drop=True)
    val   = pd.concat(vals).reset_index(drop=True)
    test  = pd.concat(tests).reset_index(drop=True)

    print(f"Train: {len(train):,}")
    print(f"Val  : {len(val):,}")
    print(f"Test : {len(test):,}")

    return train, val, test


# ─────────────────────────────────────────────────────────────
# STEP 4 — CLEAN AFTER SPLIT (IMPORTANT)
# ─────────────────────────────────────────────────────────────
def clean_after_split(df: pd.DataFrame, features: List[str]) -> pd.DataFrame:
    needed_cols = features + [
        TARGET_REGRESSION,
        TARGET_CLASSIFICATION
    ]

    df = df.dropna(subset=[c for c in needed_cols if c in df.columns])

    return df


# ─────────────────────────────────────────────────────────────
# STEP 5 — XGBOOST DATA
# ─────────────────────────────────────────────────────────────
def build_xgb_data(train, val, test):
    print("\n🌲 Building XGBoost dataset...")

    feats = [f for f in XGB_FEATURES if f in train.columns]

    # Clean AFTER split
    train = clean_after_split(train, feats)
    val   = clean_after_split(val, feats)
    test  = clean_after_split(test, feats)

    X_train = train[feats].values
    X_val   = val[feats].values
    X_test  = test[feats].values

    y_train = train[TARGET_CLASSIFICATION].values
    y_val   = val[TARGET_CLASSIFICATION].values
    y_test  = test[TARGET_CLASSIFICATION].values

    joblib.dump(feats, f"{EXPORT_DIR}/xgb_feature_names.pkl")

    print(f"XGB features: {len(feats)}")

    return X_train, X_val, X_test, y_train, y_val, y_test


# ─────────────────────────────────────────────────────────────
# STEP 6 — LSTM DATA
# ─────────────────────────────────────────────────────────────
def build_lstm_data(train, val, test, window=48, horizon=24):
    print("\n🧠 Building LSTM dataset...")

    feats = [f for f in LSTM_FEATURES if f in train.columns]

    # Clean AFTER split
    train = clean_after_split(train, feats)
    val   = clean_after_split(val, feats)
    test  = clean_after_split(test, feats)

    scaler_X = MinMaxScaler()
    scaler_y = MinMaxScaler()

    scaler_X.fit(train[feats])
    scaler_y.fit(train[[TARGET_REGRESSION]])

    def make_sequences(df_subset):
        Xs, ys = [], []

        for _, group in df_subset.groupby("village"):
            group = group.sort_values("timestamp")

            X = scaler_X.transform(group[feats])
            y = scaler_y.transform(group[[TARGET_REGRESSION]])

            for i in range(window, len(X) - horizon + 1):
                Xs.append(X[i - window:i])
                ys.append(y[i:i + horizon, 0])

        return np.array(Xs, dtype=np.float32), np.array(ys, dtype=np.float32)

    X_tr, y_tr = make_sequences(train)
    X_vl, y_vl = make_sequences(val)
    X_te, y_te = make_sequences(test)

    print(f"Train sequences: {X_tr.shape}")
    print(f"Val   sequences: {X_vl.shape}")
    print(f"Test  sequences: {X_te.shape}")

    # ❌ KHÔNG shuffle time-series

    joblib.dump(scaler_X, f"{EXPORT_DIR}/scaler_X.pkl")
    joblib.dump(scaler_y, f"{EXPORT_DIR}/scaler_y.pkl")
    joblib.dump(feats,    f"{EXPORT_DIR}/lstm_feature_names.pkl")

    return (X_tr, y_tr), (X_vl, y_vl), (X_te, y_te), scaler_y


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    df = load_raw_data()
    df, le = encode_labels(df)

    train, val, test = temporal_split(df)

    # Save split
    train.to_parquet(f"{EXPORT_DIR}/train.parquet", index=False)
    val.to_parquet(f"{EXPORT_DIR}/val.parquet", index=False)
    test.to_parquet(f"{EXPORT_DIR}/test.parquet", index=False)

    build_xgb_data(train, val, test)
    build_lstm_data(train, val, test)

    print("\n✅ Pipeline hoàn tất!")