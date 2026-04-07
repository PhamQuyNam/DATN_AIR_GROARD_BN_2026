import os, sys, logging
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
from datetime import datetime, timedelta

from etl.ingestion.openmeteo_air_fetcher     import collect_all_air_history
from etl.ingestion.openmeteo_weather_fetcher import collect_all_weather_history
from etl.processing.merger                  import merge_air_and_weather
from etl.processing.cleaner                 import clean_dataset

load_dotenv()
logger = logging.getLogger(__name__)
engine = create_engine(os.getenv("POSTGRES_URL"))


def hourly_update_job():
    """
    Chạy mỗi giờ: lấy dữ liệu 2 giờ gần nhất (overlap để không bỏ sót),
    merge, làm sạch, lưu vào DB.
    """
    now       = datetime.now()
    end_dt    = now.strftime("%Y-%m-%d")
    start_dt  = (now - timedelta(hours=2)).strftime("%Y-%m-%d")

    logger.info(f"Bắt đầu hourly update: {start_dt} → {end_dt}")

    try:
        df_air     = collect_all_air_history(start_dt, end_dt)
        df_weather = collect_all_weather_history(start_dt, end_dt)

        if df_air.empty:
            logger.warning("Không có dữ liệu air quality mới")
            return

        df_merged = merge_air_and_weather(df_air, df_weather)
        df_clean  = clean_dataset(df_merged)

        # Chỉ lưu dữ liệu thực (không phải forecast)
        df_real = df_clean[df_clean.get("is_forecast", False) == False]

        df_real["timestamp"] = pd.to_datetime(df_real["timestamp"], utc=True)
        df_real.to_sql(
            "aqi_records", engine,
            if_exists="append",
            index=False,
            method="multi",
            chunksize=100
        )
        logger.info(f"Đã lưu {len(df_real)} records mới")

    except Exception as e:
        logger.error(f"Lỗi hourly job: {e}", exc_info=True)