import pandas as pd
import numpy as np
import pathlib
import logging

# Cấu hình logging để theo dõi tiến trình
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def calculate_vn_aqi(pm25):
    """
    Tính AQI PM2.5 theo Quyết định 1459/QĐ-TCMT (Việt Nam).
    Đây chính là giá trị 'aqi_current'.
    """
    if pd.isna(pm25) or pm25 < 0: return np.nan
    if pm25 <= 25:   return (50 - 0) / (25 - 0) * (pm25 - 0) + 0
    if pm25 <= 50:   return (100 - 51) / (50 - 25.1) * (pm25 - 25.1) + 51
    if pm25 <= 80:   return (150 - 101) / (80 - 50.1) * (pm25 - 50.1) + 101
    if pm25 <= 150:  return (200 - 151) / (150 - 80.1) * (pm25 - 80.1) + 151
    if pm25 <= 250:  return (300 - 201) / (250 - 150.1) * (pm25 - 150.1) + 201
    if pm25 <= 350:  return (400 - 301) / (350 - 250.1) * (pm25 - 250.1) + 301
    return (500 - 401) / (500 - 350.1) * (pm25 - 350.1) + 401


def apply_feature_engineering(df: pd.DataFrame) -> pd.DataFrame:
    """
    Thực hiện tính toán các features mới: aqi_current, lags, rolling, và time encoding.
    """
    df = df.copy()

    # 1. Đảm bảo định dạng thời gian và sắp xếp theo làng để tính chuỗi thời gian chính xác
    df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_localize(None)
    df = df.sort_values(['village', 'timestamp']).reset_index(drop=True)

    # 2. TÍNH AQI CURRENT (Dựa trên nồng độ PM2.5 hiện tại)
    logger.info("Đang tính toán aqi_current...")
    df['aqi_current'] = df['pm25'].apply(calculate_vn_aqi)

    # 3. TIME ENCODING (hour_sin, hour_cos)
    # Giúp mô hình học tính chu kỳ ngày/đêm
    df['hour'] = df['timestamp'].dt.hour
    df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24)
    df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24)

    # 4. LAG FEATURES (aqi_lag1h, aqi_lag3h)
    # Lấy giá trị AQI của 1 giờ và 3 giờ trước đó
    for lag in [1, 3]:
        df[f'aqi_lag{lag}h'] = df.groupby('village')['aqi_current'].shift(lag)

    # 5. ROLLING FEATURES (aqi_roll3h, aqi_roll6h)
    # Tính trung bình trượt nhưng dùng shift(1) để tránh LEAKAGE thông tin hiện tại vào quá khứ
    for window in [3, 6]:
        df[f'aqi_roll{window}h'] = df.groupby('village')['aqi_current'].transform(
            lambda x: x.shift(1).rolling(window=window, min_periods=1).mean()
        )

    return df


def main():
    # Đường dẫn file đã merge (Sửa theo đúng cấu trúc máy bạn)
    base_path = pathlib.Path("C:/Users/Acer/Desktop/DATN/DATN_AIR_GROARD_BN_2026/data/merged")
    input_file = base_path / "merged_raw_data_2026.csv"

    output_dir = pathlib.Path("C:/Users/Acer/Desktop/DATN/DATN_AIR_GROARD_BN_2026/data/features")
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_file.exists():
        logger.error(f"❌ Không tìm thấy file đã merge tại: {input_file}")
        return

    # Đọc dữ liệu
    logger.info(f"Đang xử lý file: {input_file.name}")
    df_merged = pd.read_csv(input_file)

    # Thực hiện Feature Engineering
    df_final = apply_feature_engineering(df_merged)

    # Lưu kết quả
    output_path = output_dir / "final_features_dataset_2026.csv"
    df_final.to_csv(output_path, index=False, encoding="utf-8-sig")

    logger.info(f"✅ Đã tạo xong đặc trưng mới cho {len(df_final)} records.")
    logger.info(f"🚀 File lưu tại: {output_path}")


if __name__ == "__main__":
    main()