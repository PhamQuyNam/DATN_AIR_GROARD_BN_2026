"""
Chạy 1 lần duy nhất để lấy toàn bộ dữ liệu lịch sử 2 năm.
Open-Meteo archive có thể cung cấp từ năm 2022 cho air quality,
và từ 1940 cho dữ liệu thời tiết.

Cách chạy:
    python scripts/backfill_history.py
    python scripts/backfill_history.py --start 2022-01-01 --end 2024-12-31
"""
import argparse, os, sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from datetime import datetime
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

from etl.ingestion.openmeteo_air_fetcher     import collect_all_air_history
from etl.ingestion.openmeteo_weather_fetcher import collect_all_weather_history
from etl.processing.merger                  import merge_air_and_weather
from etl.processing.cleaner                 import clean_dataset
from etl.processing.validator               import validate_dataset

load_dotenv()
engine = create_engine(os.getenv("POSTGRES_URL"))


def run_backfill(start_date: str, end_date: str):
    print(f"\n{'='*55}")
    print(f"BACKFILL: {start_date} → {end_date}")
    print(f"{'='*55}\n")

    # ── Bước 1: Thu thập air quality ──────────────────────────
    print("[1/5] Thu thập dữ liệu chất lượng không khí...")
    df_air = collect_all_air_history(start_date, end_date)
    print(f"      → {len(df_air):,} records air quality\n")

    # ── Bước 2: Thu thập thời tiết ────────────────────────────
    print("[2/5] Thu thập dữ liệu thời tiết...")
    df_weather = collect_all_weather_history(start_date, end_date)
    print(f"      → {len(df_weather):,} records thời tiết\n")

    # ── Bước 3: Ghép 2 nguồn ─────────────────────────────────
    print("[3/5] Ghép dữ liệu air + weather...")
    df_merged = merge_air_and_weather(df_air, df_weather)
    print(f"      → {len(df_merged):,} records sau khi merge\n")

    # ── Bước 4: Làm sạch ─────────────────────────────────────
    print("[4/5] Làm sạch dữ liệu...")
    df_clean = clean_dataset(df_merged)
    print(f"      → {len(df_clean):,} records sau khi clean\n")

    # ── Lưu raw và processed ──────────────────────────────────
    os.makedirs(PROJECT_ROOT / "data/raw/air_quality", exist_ok=True)
    os.makedirs(PROJECT_ROOT / "data/raw/weather",     exist_ok=True)
    os.makedirs(PROJECT_ROOT / "data/processed",       exist_ok=True)

    df_air.to_csv(
        PROJECT_ROOT / f"data/raw/air_quality/history_{start_date}_{end_date}.csv",
        index=False
    )
    df_weather.to_csv(
        PROJECT_ROOT / f"data/raw/weather/history_{start_date}_{end_date}.csv",
        index=False
    )
    df_clean.to_csv(PROJECT_ROOT / "data/processed/merged_clean.csv", index=False)
    df_clean.to_parquet(PROJECT_ROOT / "data/processed/merged_clean.parquet", index=False)

    # ── Bước 5: Lưu vào PostgreSQL ───────────────────────────
    print("[5/5] Lưu vào PostgreSQL (TimescaleDB)...")
    df_db = df_clean[df_clean["is_forecast"] == False].copy()
    df_db["timestamp"] = pd.to_datetime(df_db["timestamp"], utc=True)

    df_db.to_sql(
        "aqi_records", engine,
        if_exists="replace",
        index=False,
        method="multi",
        chunksize=500
    )
    print(f"      → Đã lưu {len(df_db):,} records vào DB\n")

    # ── Báo cáo kết quả ──────────────────────────────────────
    print("="*55)
    print("KẾT QUẢ BACKFILL")
    print("="*55)
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT
                village,
                COUNT(*)                         AS so_records,
                MIN(timestamp)::date             AS tu_ngay,
                MAX(timestamp)::date             AS den_ngay,
                ROUND(AVG(pm25)::numeric, 2)     AS pm25_tb,
                ROUND(AVG(temperature)::numeric, 1) AS nhiet_do_tb
            FROM aqi_records
            GROUP BY village
            ORDER BY village
        """)).fetchall()

    header = f"{'Làng nghề':<16}{'Records':>9}{'Từ ngày':>12}{'Đến ngày':>12}{'PM2.5TB':>9}{'Nhiệt độ':>10}"
    print(header)
    print("-" * len(header))
    for r in rows:
        print(f"{r[0]:<16}{r[1]:>9}{str(r[2]):>12}{str(r[3]):>12}"
              f"{str(r[4]):>9}{str(r[5]):>10}")

    print("\nBackfill hoàn thành!")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Backfill dữ liệu lịch sử")
    parser.add_argument("--start", default="2022-01-01",
                        help="Ngày bắt đầu YYYY-MM-DD")
    parser.add_argument("--end",
                        default=datetime.now().strftime("%Y-%m-%d"),
                        help="Ngày kết thúc YYYY-MM-DD")
    args = parser.parse_args()
    run_backfill(args.start, args.end)