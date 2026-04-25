"""
etl/ingestion/openmeteo_weather_fetcher.py
"""
import time
import logging
import pathlib
import requests
import pandas as pd
from datetime import datetime

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

COL_RENAME = {
    "temperature_2m":       "temperature",
    "relative_humidity_2m": "humidity",
    "wind_speed_10m":       "wind_speed",
    "wind_direction_10m":   "wind_dir",
    "precipitation":        "precipitation",
    "surface_pressure":     "pressure",
    "cloud_cover":          "cloud_cover",
    "visibility":           "visibility",
}

ARCHIVE_URL = "https://archive-api.open-meteo.com/v1/archive"

def fetch_weather_history(village: dict, start_date: str, end_date: str) -> pd.DataFrame:
    params = {
        "latitude": village["lat"],
        "longitude": village["lon"],
        "hourly": ",".join(COL_RENAME.keys()),
        "start_date": start_date,
        "end_date": end_date,
        "timezone": "Asia/Ho_Chi_Minh"
    }

    max_retries = 5
    for attempt in range(max_retries):
        try:
            resp = requests.get(ARCHIVE_URL, params=params, timeout=30)
            resp.raise_for_status()
            break
        except Exception as e:
            if attempt < max_retries - 1:
                time.sleep(2 ** (attempt + 1))
                continue
            return pd.DataFrame()

    data = resp.json().get("hourly", {})
    if not data: return pd.DataFrame()

    df = pd.DataFrame({"timestamp": pd.to_datetime(data["time"])})
    df["timestamp"] = df["timestamp"].dt.tz_localize(None)

    for api_col, clean_col in COL_RENAME.items():
        if api_col in data:
            df[clean_col] = data[api_col]

    df["village"] = village["name"]
    return df

def collect_and_save_weather(villages_list, start_date, end_date):
    """Thu thập và lưu dữ liệu vào thư mục data/raw/weather"""
    output_dir = pathlib.Path("C:/Users/Acer/Desktop/DATN/DATN_AIR_GROARD_BN_2026/data/raw/weather")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    all_dfs = []
    for v in villages_list:
        logger.info(f"Đang lấy dữ liệu THỜI TIẾT: {v['name']}")
        df = fetch_weather_history(v, start_date, end_date)
        if not df.empty:
            all_dfs.append(df)
        time.sleep(1)
    
    if all_dfs:
        final_df = pd.concat(all_dfs, ignore_index=True)
        file_name = f"weather_{start_date}_to_{end_date}.csv"
        file_path = output_dir / file_name
        
        final_df.to_csv(file_path, index=False, encoding='utf-8-sig')
        logger.info(f"✅ Đã lưu dữ liệu thời tiết tại: {file_path}")
        return final_df
    return pd.DataFrame()


if __name__ == "__main__":
    # Import villages config
    import sys
    sys.path.insert(0, "/root" if __file__.startswith("/root") else "C:/Users/Acer/Desktop/DATN/DATN_AIR_GROARD_BN_2026")
    
    try:
        from configs.village_config import VILLAGES
    except:
        VILLAGES = []
        logger.warning("Không thể load VILLAGES config. Vui lòng cập nhật path.")
    
    if VILLAGES:
        from datetime import datetime, timedelta
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = "2024-01-01"
        
        logger.info(f"🔄 Bắt đầu thu thập dữ liệu thời tiết từ {start_date} đến {end_date}")
        collect_and_save_weather(VILLAGES, start_date, end_date)
    else:
        logger.error("❌ Không có dữ liệu villages. Kiểm tra configs/village_config.py")