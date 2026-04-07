"""
etl/ingestion/openmeteo_air_fetcher.py

Thu thập dữ liệu chất lượng không khí từ Open-Meteo Air Quality API.
Endpoint : https://air-quality-api.open-meteo.com/v1/air-quality
API key  : Không cần
Chi phí  : Miễn phí cho nghiên cứu học thuật
"""
import time
import logging

import requests
import yaml
import pandas as pd
from datetime import datetime, timedelta

# ── Import danh sách làng nghề ───────────────────────────────────────────────
try:
    from configs.village_config import (
        MONITORING_VILLAGES as VILLAGES,   # 17 làng (bỏ baseline Vọng Nguyệt)
        village_to_openmeteo_params,
    )
except ImportError:
    # Fallback khi chạy file này độc lập
    import pathlib, yaml as _yaml
    _cfg = pathlib.Path(__file__).parent.parent.parent / "configs" / "villages.yaml"
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
with open(
    pathlib.Path(__file__).parent.parent.parent / "configs" / "openmeteo.yaml"
    if "pathlib" in dir() else
    __import__("pathlib").Path(__file__).parent.parent.parent / "configs" / "openmeteo.yaml",
    encoding="utf-8"
) as _f:
    _CFG = yaml.safe_load(_f)["air_quality"]

BASE_URL   = _CFG["base_url"]       # https://air-quality-api.open-meteo.com/v1/air-quality
HOURLY_VARS = _CFG["hourly_vars"]   # pm2_5, pm10, carbon_monoxide, ...

# Mapping tên biến API → tên cột trong DB
COL_RENAME = {
    "pm2_5":                 "pm25",
    "pm10":                  "pm10",
    "carbon_monoxide":       "co",
    "nitrogen_dioxide":      "no2",
    "sulphur_dioxide":       "so2",
    "ozone":                 "o3",
    "aerosol_optical_depth": "aod",
    "dust":                  "dust",
    "european_aqi":          "aqi_eu",
    "european_aqi_pm2_5":    "aqi_eu_pm25",
    "us_aqi":                "us_aqi",
}

logger = logging.getLogger(__name__)


# ── Hàm thu thập chính ───────────────────────────────────────────────────────

def fetch_air_quality(village: dict,
                      start_date: str,
                      end_date: str) -> pd.DataFrame:
    """
    Lấy dữ liệu chất lượng không khí tại 1 làng nghề.
    Hỗ trợ retry nếu gặp 429 (rate limit).

    Args:
        village    : dict từ VILLAGES (có name, lat, lon, ...)
        start_date : "YYYY-MM-DD"
        end_date   : "YYYY-MM-DD"

    Returns:
        DataFrame với các cột timestamp, village, pm25, pm10,
        co, no2, so2, o3, aqi_eu, us_aqi, ...
    """
    params = village_to_openmeteo_params(village, {
        "hourly":     ",".join(HOURLY_VARS),
        "start_date": start_date,
        "end_date":   end_date,
    })

    # Retry logic: tối đa 5 lần nếu 429 (rate limit)
    max_retries = 8
    for attempt in range(max_retries):
        try:
            resp = requests.get(BASE_URL, params=params, timeout=30)
            resp.raise_for_status()
            break  # Thành công, thoát khỏi loop
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 429 and attempt < max_retries - 1:
                wait_time = 2 ** (attempt + 1)  # Exponential backoff: 2, 4, 8, 16, 32 giây
                logger.warning(f"  [{village['name']}] Rate limit (429), chờ {wait_time}s...")
                time.sleep(wait_time)
                continue
            else:
                logger.error(f"  [{village['name']}] Lỗi API: {e}")
                return pd.DataFrame()
        except requests.RequestException as e:
            logger.error(f"  [{village['name']}] Lỗi kết nối: {e}")
            return pd.DataFrame()

    hourly = resp.json().get("hourly", {})
    if not hourly or "time" not in hourly:
        logger.warning(f"  [{village['name']}] Không có dữ liệu air quality")
        return pd.DataFrame()

    df = pd.DataFrame({"timestamp": pd.to_datetime(hourly["time"])})

    for api_col, clean_col in COL_RENAME.items():
        if api_col in hourly:
            df[clean_col] = hourly[api_col]

    df["village"]      = village["name"]
    df["village_id"]   = village["id"]
    df["lat"]          = village["lat"]
    df["lon"]          = village["lon"]
    df["craft_type"]   = village.get("craft_type", "")
    df["source"]       = "open-meteo-air"
    df["is_forecast"]  = False

    return df


def fetch_air_quality_forecast(village: dict,
                               forecast_days: int = 5) -> pd.DataFrame:
    """
    Lấy dự báo chất lượng không khí N ngày tới.
    Dùng cho tính năng hiển thị forecast trên frontend.

    Args:
        village       : dict làng nghề
        forecast_days : số ngày dự báo (mặc định 5)
    """
    params = village_to_openmeteo_params(village, {
        "hourly":        ",".join(HOURLY_VARS),
        "forecast_days": forecast_days,
    })

    try:
        resp = requests.get(BASE_URL, params=params, timeout=30)
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
    df["source"]      = "open-meteo-air-forecast"

    return df


# ── Hàm thu thập tất cả làng nghề ────────────────────────────────────────────

def collect_all_air_history(start_date: str,
                            end_date: str) -> pd.DataFrame:
    """
    Thu thập lịch sử air quality cho toàn bộ 17 làng nghề.
    Vọng Nguyệt (baseline) được tự động loại trừ bởi MONITORING_VILLAGES.

    Args:
        start_date : "YYYY-MM-DD"
        end_date   : "YYYY-MM-DD"

    Returns:
        DataFrame đã gộp, sắp xếp theo village + timestamp
    """
    logger.info(f"Thu thập air quality {len(VILLAGES)} làng nghề: "
                f"{start_date} → {end_date}")

    all_data = []
    for i, village in enumerate(VILLAGES, 1):
        logger.info(f"  [{i:02d}/{len(VILLAGES)}] {village['name']} "
                    f"({village['craft_type']})")
        df = fetch_air_quality(village, start_date, end_date)

        if not df.empty:
            all_data.append(df)
            pm25_mean = df["pm25"].mean() if "pm25" in df.columns else float("nan")
            logger.info(f"       → {len(df):,} records  |  "
                        f"PM2.5 TB = {pm25_mean:.1f} µg/m³")
        else:
            logger.warning(f"       → Không có dữ liệu!")

        time.sleep(3.5)   # Tăng delay để tránh rate limit Open-Meteo (429)

    if not all_data:
        logger.error("Không thu thập được dữ liệu từ bất kỳ làng nghề nào!")
        return pd.DataFrame()

    final = pd.concat(all_data, ignore_index=True)
    final = final.drop_duplicates(subset=["timestamp", "village"])
    final = final.sort_values(["village", "timestamp"]).reset_index(drop=True)

    logger.info(f"Tổng cộng: {len(final):,} records từ {final['village'].nunique()} làng nghề")
    return final


def collect_all_air_current() -> pd.DataFrame:
    """
    Lấy dữ liệu air quality hiện tại (hôm nay).
    Dùng trong hourly scheduler job.
    """
    today = datetime.now().strftime("%Y-%m-%d")
    return collect_all_air_history(today, today)


def collect_all_air_forecast(forecast_days: int = 5) -> pd.DataFrame:
    """Thu thập dự báo air quality cho tất cả làng nghề."""
    all_data = []
    for village in VILLAGES:
        df = fetch_air_quality_forecast(village, forecast_days)
        if not df.empty:
            all_data.append(df)
        time.sleep(0.5)

    return pd.concat(all_data, ignore_index=True) if all_data else pd.DataFrame()


# ── Test khi chạy độc lập ────────────────────────────────────────────────────
if __name__ == "__main__":
    import pathlib
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s"
    )

    today    = datetime.now().strftime("%Y-%m-%d")
    week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")

    print(f"\n=== Test Air Quality Fetcher ===")
    print(f"Số làng nghề sẽ thu thập: {len(VILLAGES)}")
    for v in VILLAGES:
        print(f"  [{v['id']:02d}] {v['name']:<18} lat={v['lat']}, lon={v['lon']}")

    print(f"\nThu thập dữ liệu 7 ngày gần nhất ({week_ago} → {today})...")
    df = collect_all_air_history(week_ago, today)

    if not df.empty:
        print(f"\nKết quả:")
        print(df.groupby("village")[["pm25", "no2", "so2", "co", "o3"]].mean().round(2))
    else:
        print("Không có dữ liệu!")