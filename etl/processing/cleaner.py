"""
etl/processing/cleaner.py

Làm sạch dataset sau khi merge air quality + weather từ Open-Meteo.
Xử lý: missing values, outlier, kiểu dữ liệu, duplicate.
"""
import logging
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

# ── Ngưỡng hợp lệ cho từng chỉ số (theo QCVN + thực tế đo lường) ──────────
VALID_RANGES = {
    "pm25":        (0.0,   1000.0),   # µg/m³
    "pm10":        (0.0,   2000.0),   # µg/m³
    "so2":         (0.0,   2000.0),   # µg/m³
    "no2":         (0.0,   1000.0),   # µg/m³
    "co":          (0.0,  100000.0),  # µg/m³ (CO đơn vị lớn hơn)
    "o3":          (0.0,    500.0),   # µg/m³
    "aqi_eu":      (0.0,    500.0),
    "us_aqi":      (0.0,    500.0),
    "temperature": (-10.0,   50.0),   # °C (Bắc Ninh không dưới -10)
    "humidity":    (0.0,    100.0),   # %
    "wind_speed":  (0.0,     50.0),   # m/s
    "wind_dir":    (0.0,    360.0),   # độ
    "pressure":    (900.0, 1100.0),   # hPa
    "precipitation":(0.0,   200.0),   # mm
    "cloud_cover": (0.0,    100.0),   # %
}

# Các cột bắt buộc phải có trong dataset
REQUIRED_COLS = ["timestamp", "village", "pm25"]

# Các cột air quality dùng để kiểm tra "có ít nhất 1 giá trị"
AQI_COLS = ["pm25", "pm10", "so2", "no2", "co", "o3"]


# ── Hàm chính ───────────────────────────────────────────────────────────────

def clean_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """
    Pipeline làm sạch hoàn chỉnh. Gọi tuần tự các bước:
      1. Kiểm tra cột bắt buộc
      2. Chuẩn hóa kiểu dữ liệu
      3. Loại bỏ duplicate
      4. Loại hàng không có bất kỳ chỉ số AQI nào
      5. Thay outlier bằng NaN
      6. Nội suy missing values
      7. Loại bỏ hàng vẫn thiếu pm25 sau nội suy
      8. Thêm các cột phái sinh hữu ích
    """
    original_len = len(df)
    logger.info(f"Bắt đầu làm sạch: {original_len:,} records")

    df = df.copy()
    df = _check_required_columns(df)
    df = _cast_types(df)
    df = _remove_duplicates(df)
    df = _drop_all_aqi_missing(df)
    df = _replace_outliers_with_nan(df)
    df = _interpolate_missing(df)
    df = _drop_remaining_missing_pm25(df)
    df = _add_derived_features(df)

    logger.info(f"Làm sạch hoàn tất: {original_len:,} → {len(df):,} records "
                f"(loại {original_len - len(df):,})")
    return df


# ── Các bước làm sạch ───────────────────────────────────────────────────────

def _check_required_columns(df: pd.DataFrame) -> pd.DataFrame:
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset thiếu cột bắt buộc: {missing}")
    return df


def _cast_types(df: pd.DataFrame) -> pd.DataFrame:
    """Chuẩn hóa kiểu dữ liệu cho tất cả các cột."""
    # timestamp → UTC-aware datetime
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")

    # Các cột số → float
    numeric_cols = list(VALID_RANGES.keys())
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # village → string, strip khoảng trắng
    df["village"] = df["village"].astype(str).str.strip()

    return df


def _remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """Loại bỏ hàng trùng timestamp + village, giữ hàng đầu tiên."""
    before = len(df)
    df = df.drop_duplicates(subset=["timestamp", "village"], keep="first")
    dropped = before - len(df)
    if dropped > 0:
        logger.debug(f"  Loại {dropped:,} hàng duplicate")
    return df.sort_values(["village", "timestamp"]).reset_index(drop=True)


def _drop_all_aqi_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Loại hàng không có bất kỳ chỉ số AQI nào."""
    existing_aqi_cols = [c for c in AQI_COLS if c in df.columns]
    if not existing_aqi_cols:
        return df
    before = len(df)
    mask = df[existing_aqi_cols].isna().all(axis=1)
    df = df[~mask]
    dropped = before - len(df)
    if dropped > 0:
        logger.debug(f"  Loại {dropped:,} hàng không có dữ liệu AQI")
    return df


def _replace_outliers_with_nan(df: pd.DataFrame) -> pd.DataFrame:
    """
    Thay giá trị nằm ngoài ngưỡng hợp lệ bằng NaN.
    Dùng ngưỡng cứng từ VALID_RANGES thay vì IQR để giữ đúng ngữ nghĩa.
    """
    total_replaced = 0
    for col, (lo, hi) in VALID_RANGES.items():
        if col not in df.columns:
            continue
        mask = (df[col] < lo) | (df[col] > hi)
        count = mask.sum()
        if count > 0:
            df.loc[mask, col] = np.nan
            total_replaced += count
            logger.debug(f"  Outlier [{col}]: {count} giá trị → NaN")

    if total_replaced > 0:
        logger.info(f"  Tổng outlier thay thế: {total_replaced:,} giá trị")
    return df


def _interpolate_missing(df: pd.DataFrame) -> pd.DataFrame:
    """
    Nội suy missing values theo từng làng nghề.
    - Khoảng trống ≤ 3 giờ: linear interpolation
    - Khoảng trống > 3 giờ: giữ NaN (không nội suy xa)
    """
    numeric_cols = [c for c in VALID_RANGES.keys() if c in df.columns]

    filled_groups = []
    for village, group in df.groupby("village"):
        group = group.sort_values("timestamp").copy()

        for col in numeric_cols:
            # Đếm NaN liên tiếp — chỉ fill nếu khoảng trống ≤ 3
            group[col] = group[col].interpolate(
                method="linear",
                limit=3,          # Tối đa 3 giờ liên tiếp
                limit_direction="both"
            )

        filled_groups.append(group)

    result = pd.concat(filled_groups, ignore_index=True)
    missing_after = result[numeric_cols].isna().sum().sum()
    logger.info(f"  Sau nội suy: còn {missing_after:,} giá trị NaN")
    return result


def _drop_remaining_missing_pm25(df: pd.DataFrame) -> pd.DataFrame:
    """Loại hàng vẫn thiếu pm25 sau khi đã nội suy."""
    before = len(df)
    df = df.dropna(subset=["pm25"])
    dropped = before - len(df)
    if dropped > 0:
        logger.debug(f"  Loại {dropped:,} hàng vẫn thiếu PM2.5 sau nội suy")
    return df


def _add_derived_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Thêm các cột phái sinh hữu ích cho ML:
    - hour, day_of_week, month, is_weekend
    - wind_u, wind_v (thành phần vector của gió)
    - pm25_category (nhãn phân loại QCVN)
    """
    df["hour"]         = df["timestamp"].dt.hour
    df["day_of_week"]  = df["timestamp"].dt.dayofweek   # 0=Thứ 2, 6=CN
    df["month"]        = df["timestamp"].dt.month
    df["is_weekend"]   = (df["day_of_week"] >= 5).astype(int)
    df["is_rush_hour"] = df["hour"].isin([7, 8, 17, 18]).astype(int)

    # Phân rã hướng gió thành 2 thành phần sin/cos
    # (tránh vấn đề 0° và 360° là cùng hướng nhưng giá trị khác nhau)
    if "wind_dir" in df.columns:
        wind_rad = np.deg2rad(df["wind_dir"].fillna(0))
        df["wind_sin"] = np.sin(wind_rad)
        df["wind_cos"] = np.cos(wind_rad)

    # Phân loại PM2.5 theo QCVN 05:2023
    if "pm25" in df.columns:
        df["pm25_category"] = pd.cut(
            df["pm25"],
            bins=[-np.inf, 12, 35.4, 55.4, 150.4, 250.4, np.inf],
            labels=["Tốt", "Trung bình", "Kém nhạy cảm", "Kém", "Xấu", "Nguy hại"],
            right=True
        )

    return df


# ── Hàm tiện ích ─────────────────────────────────────────────────────────────

def get_cleaning_report(df_before: pd.DataFrame,
                        df_after: pd.DataFrame) -> dict:
    """Tạo báo cáo tóm tắt quá trình làm sạch."""
    return {
        "records_before":  len(df_before),
        "records_after":   len(df_after),
        "records_dropped": len(df_before) - len(df_after),
        "drop_rate_pct":   round((1 - len(df_after) / len(df_before)) * 100, 2),
        "missing_before":  df_before.isna().sum().to_dict(),
        "missing_after":   df_after.isna().sum().to_dict(),
        "villages":        df_after["village"].unique().tolist(),
        "date_range": {
            "start": str(df_after["timestamp"].min()),
            "end":   str(df_after["timestamp"].max()),
        }
    }


# ── Test nhanh ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s [%(levelname)s] %(message)s")

    # Tạo dữ liệu giả để test
    import sys, os
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

    sample = pd.DataFrame({
        "timestamp": pd.date_range("2024-01-01", periods=50, freq="h", tz="UTC"),
        "village":   ["Phong Khê"] * 50,
        "pm25":      [25.0, np.nan, np.nan, 9999.0, 35.0] * 10,  # có outlier + NaN
        "pm10":      [40.0] * 50,
        "so2":       [5.0] * 50,
        "no2":       [10.0] * 50,
        "co":        [500.0] * 50,
        "o3":        [60.0] * 50,
        "temperature": [28.0] * 50,
        "humidity":    [75.0] * 50,
        "wind_speed":  [2.5] * 50,
        "wind_dir":    [180.0] * 50,
    })

    print("=== Test Cleaner ===")
    print(f"Trước: {len(sample)} records, PM2.5 NaN={sample['pm25'].isna().sum()}")

    cleaned = clean_dataset(sample)
    print(f"Sau  : {len(cleaned)} records, PM2.5 NaN={cleaned['pm25'].isna().sum()}")
    print(f"\nCột mới thêm: {[c for c in cleaned.columns if c not in sample.columns]}")
    print(cleaned[["timestamp","village","pm25","pm25_category","hour","wind_sin"]].head(8))