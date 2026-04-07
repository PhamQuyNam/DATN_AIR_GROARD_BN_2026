# ml_training/preprocessing/feature_engineer.py
import numpy as np
import pandas as pd
from sqlalchemy import create_engine
import os
from dotenv import load_dotenv
from aqi_calculator import add_aqi_columns

load_dotenv()
engine = create_engine(os.getenv("POSTGRES_URL"))

def build_feature_dataset(target_col: str = "aqi_vn") -> pd.DataFrame:
    """
    Tạo dataset hoàn chỉnh cho training:
    1. Đọc từ DB
    2. Tính AQI theo QCVN
    3. Thêm time features
    4. Thêm lag features (t-1, t-3, t-6, t-12, t-24)
    5. Thêm rolling features (3h, 6h, 24h)
    6. Encode village
    7. Xuất file cho ML
    """
    print("Đọc dữ liệu từ PostgreSQL...")
    df = pd.read_sql(
        "SELECT * FROM aqi_records WHERE is_forecast = FALSE "
        "ORDER BY village, timestamp",
        engine, parse_dates=["timestamp"]
    )
    print(f"  {len(df):,} records từ {df['village'].nunique()} làng")

    # ── Tính AQI theo QCVN ───────────────────────────────────────────────────
    print("Tính AQI theo QCVN 05:2023...")
    df = add_aqi_columns(df)

    # ── Time features ─────────────────────────────────────────────────────────
    print("Thêm time features...")
    df["hour"]         = df["timestamp"].dt.hour
    df["day_of_week"]  = df["timestamp"].dt.dayofweek
    df["month"]        = df["timestamp"].dt.month
    df["is_weekend"]   = (df["day_of_week"] >= 5).astype(int)
    df["is_rush_hour"] = df["hour"].isin([7, 8, 17, 18]).astype(int)
    # Encode tuần hoàn (tốt hơn dùng số nguyên cho ML)
    df["hour_sin"]     = np.sin(2 * np.pi * df["hour"]   / 24)
    df["hour_cos"]     = np.cos(2 * np.pi * df["hour"]   / 24)
    df["month_sin"]    = np.sin(2 * np.pi * df["month"]  / 12)
    df["month_cos"]    = np.cos(2 * np.pi * df["month"]  / 12)
    df["dow_sin"]      = np.sin(2 * np.pi * df["day_of_week"] / 7)
    df["dow_cos"]      = np.cos(2 * np.pi * df["day_of_week"] / 7)

    # ── Encode village ────────────────────────────────────────────────────────
    df["village_encoded"] = pd.Categorical(df["village"]).codes

    # ── Lag + Rolling theo từng làng ─────────────────────────────────────────
    print("Tính lag và rolling features theo làng nghề...")
    lag_hours    = [1, 3, 6, 12, 24, 48]
    rolling_wins = [3, 6, 24]

    groups = []
    for village, grp in df.groupby("village"):
        grp = grp.sort_values("timestamp").copy()

        # Lag features
        for h in lag_hours:
            grp[f"pm25_lag{h}h"]  = grp["pm25"].shift(h)
            grp[f"aqi_lag{h}h"]   = grp[target_col].shift(h)

        # Rolling mean
        for w in rolling_wins:
            grp[f"pm25_roll{w}h"] = grp["pm25"].rolling(w, min_periods=1).mean()
            grp[f"aqi_roll{w}h"]  = grp[target_col].rolling(w, min_periods=1).mean()

        # Rolling std (đo độ biến động)
        grp["pm25_roll24h_std"] = grp["pm25"].rolling(24, min_periods=6).std()

        groups.append(grp)

    df = pd.concat(groups, ignore_index=True)

    # ── Loại bỏ hàng thiếu target ─────────────────────────────────────────────
    df = df.dropna(subset=[target_col])

    # ── Xuất dataset ──────────────────────────────────────────────────────────
    os.makedirs("../data/exports", exist_ok=True)
    df.to_parquet("../data/exports/ml_dataset.parquet", index=False)
    df.to_csv("../data/exports/ml_dataset.csv", index=False)

    print(f"\nDataset hoàn chỉnh: {len(df):,} records × {len(df.columns)} features")
    print(f"Xuất: data/exports/ml_dataset.parquet")

    # In danh sách features
    feature_cols = [c for c in df.columns if c not in
                    ["timestamp", "village", "source", "aqi_level",
                     "aqi_color", "dominant_pollutant"]]
    print(f"\nFeatures ({len(feature_cols)}):")
    for i, col in enumerate(feature_cols, 1):
        print(f"  {i:3d}. {col}")

    return df


if __name__ == "__main__":
    df = build_feature_dataset()
    print(f"\nPhân phối AQI:\n{df['aqi_level'].value_counts()}")