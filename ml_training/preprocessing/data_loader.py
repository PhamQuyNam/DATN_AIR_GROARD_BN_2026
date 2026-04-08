"""
ml_training/preprocessing/data_splitter.py
Tải dataset, chọn features, split train/val/test
cho cả 2 pipeline XGBoost và LSTM.
"""
import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler, LabelEncoder
import joblib, os

# ── Đường dẫn ────────────────────────────────────────────────────────────────
DATASET_PATH = "../data/exports/ml_dataset.parquet"
EXPORT_DIR   = "../data/exports"
os.makedirs(EXPORT_DIR, exist_ok=True)

# ── Cấu hình features ────────────────────────────────────────────────────────
# Target
TARGET_REGRESSION      = "aqi_vn"        # Dùng cho LSTM (hồi quy)
TARGET_CLASSIFICATION  = "aqi_level"     # Dùng cho XGBoost (phân loại)

# Features dùng chung cho cả 2 mô hình
BASE_FEATURES = [
    # Chất ô nhiễm
    "pm25", "pm10", "so2", "no2", "co", "o3",
    # Thời tiết
    "temperature", "humidity", "wind_speed", "wind_sin", "wind_cos",
    "precipitation", "pressure", "cloud_cover",
    # Thời gian (encode tuần hoàn)
    "hour_sin", "hour_cos", "month_sin", "month_cos",
    "dow_sin", "dow_cos", "is_weekend", "is_rush_hour",
    # Lag features (lịch sử AQI)
    "pm25_lag1h",  "aqi_lag1h",
    "pm25_lag3h",  "aqi_lag3h",
    "pm25_lag6h",  "aqi_lag6h",
    "pm25_lag12h", "aqi_lag12h",
    "pm25_lag24h", "aqi_lag24h",
    "pm25_lag48h", "aqi_lag48h",
    # Rolling features
    "pm25_roll3h",  "aqi_roll3h",
    "pm25_roll6h",  "aqi_roll6h",
    "pm25_roll24h", "aqi_roll24h",
    "pm25_roll24h_std",
    # Village
    "village_encoded",
]

# XGBoost thêm sub-AQI từng chất (giúp SHAP hiểu rõ hơn)
XGB_EXTRA_FEATURES = ["aqi_pm25", "aqi_pm10", "aqi_so2",
                       "aqi_no2", "aqi_co", "aqi_o3"]
XGB_FEATURES = BASE_FEATURES + XGB_EXTRA_FEATURES

# LSTM chỉ dùng BASE_FEATURES (để tránh data leakage từ sub-AQI)
LSTM_FEATURES = BASE_FEATURES


def load_and_prepare():
    """Load dataset, xử lý NaN, encode label."""
    print("Đang tải dataset...")
    df = pd.read_parquet(DATASET_PATH)

    # Bỏ các cột không cần
    drop_cols = ["source", "aqi_color", "dominant_pollutant",
                 "is_forecast", "dust", "aod", "lat", "lon",
                 "pm25_category"]
    df = df.drop(columns=[c for c in drop_cols if c in df.columns])

    # Đảm bảo timestamp đúng thứ tự
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(["village", "timestamp"]).reset_index(drop=True)

    # Encode target phân loại
    label_order = ["Tốt", "Trung bình", "Kém (nhạy cảm)",
                   "Kém", "Rất xấu", "Nguy hại"]
    le = LabelEncoder()
    le.classes_ = np.array(label_order)
    df["aqi_level_encoded"] = le.transform(
        df["aqi_level"].fillna("Trung bình")
    )

    # Loại NaN trong features chính
    all_needed = list(set(XGB_FEATURES + LSTM_FEATURES +
                          [TARGET_REGRESSION, "aqi_level_encoded",
                           "timestamp", "village"]))
    df = df.dropna(subset=[c for c in all_needed if c in df.columns])

    print(f"Dataset sau xử lý: {len(df):,} records")
    print(f"Phân phối AQI:\n{df['aqi_level'].value_counts()}\n")

    return df, le


def temporal_split(df: pd.DataFrame):
    """
    Chia theo thời gian (QUAN TRỌNG với time-series):
    - Không được shuffle ngẫu nhiên!
    - Train: 70% thời gian đầu
    - Val  : 15% tiếp theo
    - Test : 15% cuối cùng
    """
    df = df.sort_values("timestamp").reset_index(drop=True)
    n = len(df)
    i_train = int(n * 0.70)
    i_val   = int(n * 0.85)

    train = df.iloc[:i_train].copy()
    val   = df.iloc[i_train:i_val].copy()
    test  = df.iloc[i_val:].copy()

    print(f"Train : {len(train):,} records "
          f"({train['timestamp'].min().date()} → {train['timestamp'].max().date()})")
    print(f"Val   : {len(val):,} records "
          f"({val['timestamp'].min().date()} → {val['timestamp'].max().date()})")
    print(f"Test  : {len(test):,} records "
          f"({test['timestamp'].min().date()} → {test['timestamp'].max().date()})")
    return train, val, test


def build_xgb_data(train, val, test):
    """Chuẩn bị X, y cho XGBoost. Không cần scale với tree model."""
    feats = [f for f in XGB_FEATURES if f in train.columns]

    X_train = train[feats].values
    X_val   = val[feats].values
    X_test  = test[feats].values
    y_train = train["aqi_level_encoded"].values
    y_val   = val["aqi_level_encoded"].values
    y_test  = test["aqi_level_encoded"].values

    # Lưu tên features để dùng cho SHAP
    joblib.dump(feats, f"{EXPORT_DIR}/xgb_feature_names.pkl")
    print(f"\nXGBoost: {len(feats)} features")
    return X_train, X_val, X_test, y_train, y_val, y_test


def build_lstm_data(train, val, test,
                    window: int = 48,
                    horizon: int = 24):
    """
    Chuẩn bị sequences cho LSTM.
    - window : số giờ lịch sử đầu vào (48h)
    - horizon: số giờ cần dự báo    (24h)
    """
    feats  = [f for f in LSTM_FEATURES if f in train.columns]
    target = TARGET_REGRESSION

    # Scale features về [0, 1]
    scaler_X = MinMaxScaler()
    scaler_y = MinMaxScaler()

    # Fit TRÊN TRAIN, transform trên cả 3 tập
    X_train_s = scaler_X.fit_transform(train[feats].values)
    X_val_s   = scaler_X.transform(val[feats].values)
    X_test_s  = scaler_X.transform(test[feats].values)

    y_train_s = scaler_y.fit_transform(train[[target]].values)
    y_val_s   = scaler_y.transform(val[[target]].values)
    y_test_s  = scaler_y.transform(test[[target]].values)

    def make_sequences(X, y):
        """Tạo sliding window sequences."""
        Xs, ys = [], []
        for i in range(window, len(X) - horizon + 1):
            Xs.append(X[i - window:i])        # shape: (window, n_features)
            ys.append(y[i:i + horizon, 0])    # shape: (horizon,)
        return np.array(Xs), np.array(ys)

    print(f"\nLSTM: Tạo sequences (window={window}h, horizon={horizon}h)...")
    X_tr, y_tr = make_sequences(X_train_s, y_train_s)
    X_vl, y_vl = make_sequences(X_val_s,   y_val_s)
    X_te, y_te = make_sequences(X_test_s,  y_test_s)

    print(f"  Train sequences: {X_tr.shape}")
    print(f"  Val   sequences: {X_vl.shape}")
    print(f"  Test  sequences: {X_te.shape}")

    # Lưu scaler
    joblib.dump(scaler_X, f"{EXPORT_DIR}/scaler_X.pkl")
    joblib.dump(scaler_y, f"{EXPORT_DIR}/scaler_y.pkl")
    joblib.dump(feats,    f"{EXPORT_DIR}/lstm_feature_names.pkl")

    return (X_tr, y_tr), (X_vl, y_vl), (X_te, y_te), scaler_y


if __name__ == "__main__":
    df, le = load_and_prepare()
    train, val, test = temporal_split(df)

    # Lưu split để dùng trong notebook
    train.to_parquet(f"{EXPORT_DIR}/train.parquet", index=False)
    val.to_parquet(f"{EXPORT_DIR}/val.parquet",     index=False)
    test.to_parquet(f"{EXPORT_DIR}/test.parquet",   index=False)

    joblib.dump(le, f"{EXPORT_DIR}/label_encoder.pkl")

    build_xgb_data(train, val, test)
    build_lstm_data(train, val, test)
    print("\nXong — file đã lưu vào data/exports/")