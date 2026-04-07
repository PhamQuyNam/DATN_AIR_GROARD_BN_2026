"""
etl/ingestion/openmeteo_weather_fetcher.py

Thu thập dữ liệu thời tiết từ Open-Meteo.
- Lịch sử : archive-api.open-meteo.com  (từ năm 1940 → hôm qua)
- Forecast : api.open-meteo.com          (7–16 ngày tới)
API key   : Không cần
Chi phí   : Miễn phí
"""
import pathlib
import time
import logging

import requests
import yaml
import pandas as pd
from datetime import datetime, timedelta

# ── Import danh sách làng nghề ───────────────────────────────────────────────
try:
    from configs.village_config import (
        MONITORING_VILLAGES as VILLAGES,
        village_to_openmeteo_params,
    )
except ImportError:
    import pathlib as _pl, yaml as _yaml
    _cfg = _pl.Path(__file__).parent.parent.parent / "configs" / "villages.yaml"
    with open(_cfg, encoding="utf-8") as _f:
        VILLAGES = [v for v in _yaml.safe_load(_f)["villages"]
                    if not v.get("is_baseline", False)]

    def village_to_openmeteo_params(village, extra=None):
        p = {"latitude": village["lat"], "longitude": village["lon"],
             "timezone": "Asia/Ho_Chi_Minh"}
        if extra:
            p.update(extra)
        return p

# ── Cấu hình API ─────────────────────────────────────────────────────────────
_cfg_path = (
    pathlib.Path(__file__).parent.parent.parent / "configs" / "openmeteo.yaml"
)
with open(_cfg_path, encoding="utf-8") as _f:
    _CFG = yaml.safe_load(_f)["weather"]

FORECAST_URL = _CFG["forecast_url"]   # https://api.open-meteo.com/v1/forecast
ARCHIVE_URL  = _CFG["archive_url"]    # https://archive-api.open-meteo.com/v1/archive
HOURLY_VARS  = _CFG["hourly_vars"]    # temperature_2m, relative_humidity_2m, ...

# Mapping tên biến API → tên cột trong DB
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

logger = logging.getLogger(__name__)


# ── Hàm thu thập chính ───────────────────────────────────────────────────────

def fetch_weather_history(village: dict,
                          start_date: str,
                          end_date: str) -> pd.DataFrame:
    """
    Lấy dữ liệu thời tiết lịch sử từ Open-Meteo Archive API.
    Dữ liệu có từ năm 1940 — rất phù hợp để tạo dataset dài hạn.
    Hỗ trợ retry nếu gặp 429 (rate limit).

    Args:
        village    : dict làng nghề (có lat, lon, name)
        start_date : "YYYY-MM-DD"
        end_date   : "YYYY-MM-DD" (tối đa hôm qua — archive không có hôm nay)

    Returns:
        DataFrame với các cột: timestamp, village, temperature, humidity,
        wind_speed, wind_dir, precipitation, pressure, cloud_cover
    """
    params = village_to_openmeteo_params(village, {
        "hourly":     ",".join(HOURLY_VARS),
        "start_date": start_date,
        "end_date":   end_date,
    })

    # Retry logic: tối đa 5 lần nếu 429 (rate limit)
    max_retries = 5
    for attempt in range(max_retries):
        try:
            resp = requests.get(ARCHIVE_URL, params=params, timeout=30)
            resp.raise_for_status()
            break  # Thành công, thoát khỏi loop
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429 and attempt < max_retries - 1:
                wait_time = 2 ** (attempt + 1)  # Exponential backoff: 2, 4, 8, 16, 32 giây
                logger.warning(f"  [{village['name']}] Rate limit (429), chờ {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                logger.error(f"  [{village['name']}] Lỗi archive API: {e}")
                return pd.DataFrame()
        except requests.RequestException as e:
            logger.error(f"  [{village['name']}] Lỗi kết nối: {e}")
            return pd.DataFrame()

    hourly = resp.json().get("hourly", {})
    if not hourly or "time" not in hourly:
        logger.warning(f"  [{village['name']}] Không có dữ liệu thời tiết lịch sử")
        return pd.DataFrame()

    df = pd.DataFrame({"timestamp": pd.to_datetime(hourly["time"])})

    for api_col, clean_col in COL_RENAME.items():
        if api_col in hourly:
            df[clean_col] = hourly[api_col]

    df["village"]     = village["name"]
    df["village_id"]  = village["id"]
    df["is_forecast"] = False
    df["source"]      = "open-meteo-archive"

    return df


def fetch_weather_forecast(village: dict,
                           forecast_days: int = 7) -> pd.DataFrame:
    """
    Lấy dự báo thời tiết N ngày tới.
    Dùng làm feature đầu vào khi LSTM dự báo AQI tương lai.

    Args:
        village       : dict làng nghề
        forecast_days : số ngày dự báo (mặc định 7, tối đa 16)
    """
    params = village_to_openmeteo_params(village, {
        "hourly":        ",".join(HOURLY_VARS),
        "forecast_days": forecast_days,
    })

    try:
        resp = requests.get(FORECAST_URL, params=params, timeout=30)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"  [{village['name']}] Lỗi forecast API: {e}")
        return pd.DataFrame()

    hourly = resp.json().get("hourly", {})
    if not hourly:
        return pd.DataFrame()

    df = pd.DataFrame({"timestamp": pd.to_datetime(hourly["time"])})

    for api_col, clean_col in COL_RENAME.items():
        if api_col in hourly:
            df[clean_col] = hourly[api_col]

    df["village"]     = village["name"]
    df["village_id"]  = village["id"]
    df["is_forecast"] = True
    df["source"]      = "open-meteo-forecast"

    return df


# ── Hàm thu thập tất cả làng nghề ────────────────────────────────────────────

def collect_all_weather_history(start_date: str,
                                end_date: str) -> pd.DataFrame:
    """
    Thu thập lịch sử thời tiết cho toàn bộ 17 làng nghề.

    Args:
        start_date : "YYYY-MM-DD"
        end_date   : "YYYY-MM-DD"
    """
    logger.info(f"Thu thập thời tiết {len(VILLAGES)} làng nghề: "
                f"{start_date} → {end_date}")

    all_data = []
    for i, village in enumerate(VILLAGES, 1):
        logger.info(f"  [{i:02d}/{len(VILLAGES)}] {village['name']}")
        df = fetch_weather_history(village, start_date, end_date)

        if not df.empty:
            all_data.append(df)
            temp_mean = df["temperature"].mean() if "temperature" in df.columns else float("nan")
            logger.info(f"       → {len(df):,} records  |  "
                        f"Nhiệt độ TB = {temp_mean:.1f}°C")
        else:
            logger.warning(f"       → Không có dữ liệu!")

        time.sleep(3.5)  # Tăng delay để tránh rate limit Open-Meteo (429)

    if not all_data:
        return pd.DataFrame()

    final = pd.concat(all_data, ignore_index=True)
    final = final.drop_duplicates(subset=["timestamp", "village"])
    final = final.sort_values(["village", "timestamp"]).reset_index(drop=True)

    logger.info(f"Tổng cộng: {len(final):,} records thời tiết")
    return final


def collect_all_weather_current() -> pd.DataFrame:
    """
    Lấy dữ liệu thời tiết hôm nay.
    Dùng trong hourly scheduler job — gọi forecast_days=1 thay vì archive
    vì archive không có dữ liệu trong ngày hiện tại.
    """
    all_data = []
    for village in VILLAGES:
        df = fetch_weather_forecast(village, forecast_days=1)
        if not df.empty:
            # Chỉ lấy các giờ đã qua (không phải tương lai)
            now = pd.Timestamp.now(tz="Asia/Ho_Chi_Minh")
            df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_localize(
                "Asia/Ho_Chi_Minh", ambiguous="NaT", nonexistent="NaT"
            )
            df = df[df["timestamp"] <= now].copy()
            df["is_forecast"] = False
            df["source"]      = "open-meteo-current"
            if not df.empty:
                all_data.append(df)
        time.sleep(0.5)

    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()


def collect_all_weather_forecast(forecast_days: int = 7) -> pd.DataFrame:
    """Thu thập dự báo thời tiết cho tất cả làng nghề."""
    all_data = []
    for village in VILLAGES:
        df = fetch_weather_forecast(village, forecast_days)
        if not df.empty:
            all_data.append(df)
        time.sleep(0.5)

    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()


# ── Test khi chạy độc lập ────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    today    = datetime.now().strftime("%Y-%m-%d")
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    print(f"\n=== Test Weather Fetcher ===")
    print(f"Số làng nghề sẽ thu thập: {len(VILLAGES)}")

    print(f"\nThu thập thời tiết 7 ngày gần nhất ({week_ago} → {today})...")
    df = collect_all_weather_history(week_ago, today)

    if not df.empty:
        print(f"\nKết quả:")
        cols = [c for c in ["temperature", "humidity", "wind_speed", "pressure"]
                if c in df.columns]
        print(df.groupby("village")[cols].mean().round(2))
    else:
        print("Không có dữ liệu!")