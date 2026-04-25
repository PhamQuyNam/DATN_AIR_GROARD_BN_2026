import logging
import numpy as np
import pandas as pd
import pathlib

# Cấu hình logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# Ngưỡng hợp lệ để lọc bỏ giá trị rác từ cảm biến/API
VALID_RANGES = {
    "pm25":        (0.0, 1000.0),
    "temperature": (-10.0, 50.0),
    "humidity":    (0.0, 100.0),
    "wind_speed":  (0.0, 150.0),
    "aqi_current": (0.0, 500.0),
}

def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pipeline làm sạch dữ liệu sau Feature Engineering.
    """
    df = df.copy()
    original_len = len(df)

    # 1. Chuẩn hóa thời gian (KHÔNG dùng utc=True để giữ nguyên giờ VN)
    df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_localize(None)

    # 2. Xử lý Outliers: Chuyển các giá trị vô lý thành NaN thay vì xóa hàng ngay
    for col, (lo, hi) in VALID_RANGES.items():
        if col in df.columns:
            mask = (df[col] < lo) | (df[col] > hi)
            if mask.any():
                df.loc[mask, col] = np.nan
                logger.debug(f"  Đã chuyển {mask.sum()} giá trị outlier cột {col} thành NaN")

    # 3. Loại bỏ các dòng bị NaN ở các cột trọng yếu (Target và Features quan trọng)
    # Chúng ta bắt buộc phải bỏ các dòng NaN ở cột Lag/Rolling vì Model không học được NaN
    essential_cols = ["aqi_current", "aqi_lag1h", "aqi_roll3h"]
    df = df.dropna(subset=[c for c in essential_cols if c in df.columns])

    # 4. Phân loại AQI theo nhãn tiếng Việt (Dành cho báo cáo/phân loại)
    if "aqi_current" in df.columns:
        bins = [-1, 50, 100, 150, 200, 300, 1000]
        labels = ["Tốt", "Bình thường", "Kém", "Xấu", "Rất xấu", "Nguy hại"]
        df["aqi_category"] = pd.cut(df["aqi_current"], bins=bins, labels=labels)

    logger.info(f"Làm sạch hoàn tất: {original_len:,} → {len(df):,} records")
    return df

def main():
    # Đường dẫn file input (file chứa 27 features bạn vừa tạo)
    input_path = pathlib.Path(r"C:\Users\Acer\Desktop\DATN\DATN_AIR_GROARD_BN_2026\data\features\final_features_dataset_2026.csv")
    output_dir = pathlib.Path(r"C:\Users\Acer\Desktop\DATN\DATN_AIR_GROARD_BN_2026\data\processed")
    output_dir.mkdir(parents=True, exist_ok=True)

    if not input_path.exists():
        logger.error(f"❌ Không tìm thấy file: {input_path}")
        return

    # Đọc dữ liệu
    df = pd.read_csv(input_path)

    # Thực hiện làm sạch
    df_cleaned = clean_dataset(df)

    if len(df_cleaned) == 0:
        logger.error("⚠️ CẢNH BÁO: Dataset sau khi clean bị trống! Kiểm tra lại dữ liệu đầu vào.")
    else:
        # Lưu kết quả
        output_file = output_dir / "dataset_ready_for_ml.csv"
        df_cleaned.to_csv(output_file, index=False, encoding="utf-8-sig")
        logger.info(f"✅ HOÀN THÀNH! File sẵn sàng tại: {output_file}")
        logger.info(f"📊 Kích thước cuối cùng: {df_cleaned.shape}")

if __name__ == "__main__":
    main()