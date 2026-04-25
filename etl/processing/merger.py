import pandas as pd
import pathlib
import logging

# Cấu hình logging để theo dõi quá trình chạy
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


def run_merger():
    """
    Đọc dữ liệu từ air và weather, gộp lại và lưu vào data/merged
    """
    # 1. Định nghĩa đường dẫn
    air_path = pathlib.Path("C:/Users/Acer/Desktop/DATN/DATN_AIR_GROARD_BN_2026/data/raw/air/air_quality_2024-01-01_to_2026-04-23.csv")
    weather_path = pathlib.Path("C:/Users/Acer/Desktop/DATN/DATN_AIR_GROARD_BN_2026/data/raw/weather/weather_2024-01-01_to_2026-04-23.csv")
    output_dir = pathlib.Path("C:/Users/Acer/Desktop/DATN/DATN_AIR_GROARD_BN_2026/data/merged")

    # Tạo thư mục merged nếu chưa có
    output_dir.mkdir(parents=True, exist_ok=True)

    # 2. Kiểm tra sự tồn tại của file
    if not air_path.exists() or not weather_path.exists():
        logger.error("❌ Thiếu file dữ liệu thô. Hãy kiểm tra lại folder data/raw!")
        return

    # 3. Đọc dữ liệu
    logger.info("Đang đọc dữ liệu từ CSV...")
    df_air = pd.read_csv(air_path)
    df_weather = pd.read_csv(weather_path)

    # 4. Tiền xử lý timestamp để đảm bảo khớp nhau tuyệt đối
    df_air["timestamp"] = pd.to_datetime(df_air["timestamp"])
    df_weather["timestamp"] = pd.to_datetime(df_weather["timestamp"])

    # Loại bỏ các cột trùng lặp không cần thiết trong file weather trước khi merge
    # Chúng ta giữ lại 'timestamp' và 'village' làm khóa chính để join
    weather_cols_to_keep = [
        "timestamp", "village", "temperature", "humidity",
        "wind_speed", "wind_dir", "precipitation",
        "pressure", "cloud_cover", "visibility"
    ]
    # Chỉ lấy những cột thực sự tồn tại trong file của bạn
    weather_cols_to_keep = [c for c in weather_cols_to_keep if c in df_weather.columns]
    df_weather_subset = df_weather[weather_cols_to_keep]

    # 5. Thực hiện Merge
    # Sử dụng 'outer' join ở bước này để tránh mất dữ liệu nếu một bên bị thiếu giờ
    # Sau đó bạn sẽ Clean (Lọc bỏ hoặc nội suy) ở bước sau
    logger.info(f"Đang gộp dữ liệu cho các làng nghề...")
    merged_df = pd.merge(
        df_air,
        df_weather_subset,
        on=["timestamp", "village"],
        how="outer"
    )

    # Sắp xếp theo Làng và Thời gian để dễ theo dõi
    merged_df = merged_df.sort_values(by=["village", "timestamp"]).reset_index(drop=True)

    # 6. Lưu file
    output_file = output_dir / "merged_raw_data_2026.csv"
    merged_df.to_csv(output_file, index=False, encoding='utf-8-sig')

    logger.info(f"✅ Đã gộp thành công {len(merged_df)} dòng dữ liệu.")
    logger.info(f"🚀 File được lưu tại: {output_file}")


if __name__ == "__main__":
    run_merger()