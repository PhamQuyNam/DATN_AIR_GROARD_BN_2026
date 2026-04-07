"""
Tính chỉ số AQI theo QCVN 05:2023/BTNMT (Việt Nam).
Áp dụng công thức AQI sub-index cho từng chất ô nhiễm,
lấy giá trị lớn nhất làm AQI tổng hợp.
"""
import numpy as np
import pandas as pd

# ── Bảng ngưỡng nồng độ và AQI tương ứng theo QCVN 05:2023 ─────────────────
# Mỗi chất: list các (C_low, C_high, AQI_low, AQI_high)
# Nồng độ trung bình 24 giờ (µg/m³) trừ CO (mg/m³)

AQI_BREAKPOINTS = {
    "pm25": [   # µg/m³, trung bình 24h
        (0.0,   25.0,   0,   50),
        (25.1,  50.0,  51,  100),
        (50.1,  150.0, 101, 150),
        (150.1, 250.0, 151, 200),
        (250.1, 350.0, 201, 300),
        (350.1, 500.0, 301, 400),
    ],
    "pm10": [   # µg/m³, trung bình 24h
        (0,    50,    0,   50),
        (51,   150,  51,  100),
        (151,  250, 101,  150),
        (251,  350, 151,  200),
        (351,  420, 201,  300),
        (421,  600, 301,  400),
    ],
    "so2": [    # µg/m³, trung bình 24h
        (0,     50,   0,   50),
        (51,   150,  51,  100),
        (151,  500, 101,  150),
        (501,  750, 151,  200),
        (751, 1000, 201,  300),
        (1001,1500, 301,  400),
    ],
    "no2": [    # µg/m³, trung bình 24h
        (0,     40,   0,   50),
        (41,   100,  51,  100),
        (101,  200, 101,  150),
        (201,  400, 151,  200),
        (401,  700, 201,  300),
        (701, 1200, 301,  400),
    ],
    "co": [     # mg/m³, trung bình 8h (nếu dữ liệu µg/m³ thì ÷ 1000)
        (0,      5,    0,   50),
        (5.1,   15,   51,  100),
        (15.1,  25,  101,  150),
        (25.1,  50,  151,  200),
        (50.1, 150,  201,  300),
        (150.1,500,  301,  400),
    ],
    "o3": [     # µg/m³, trung bình 8h
        (0,     60,   0,   50),
        (61,   120,  51,  100),
        (121,  180, 101,  150),
        (181,  240, 151,  200),
        (241,  400, 201,  300),
        (401,  800, 301,  400),
    ],
}

AQI_LEVELS = [
    (0,   50,  "Tốt",              "#00e400"),
    (51,  100, "Trung bình",       "#ffff00"),
    (101, 150, "Kém (nhạy cảm)",   "#ff7e00"),
    (151, 200, "Kém",              "#ff0000"),
    (201, 300, "Rất xấu",          "#8f3f97"),
    (301, 500, "Nguy hại",         "#7e0023"),
]


def _linear_interpolate(c: float,
                        c_lo: float, c_hi: float,
                        aqi_lo: int, aqi_hi: int) -> float:
    """Công thức nội suy tuyến tính AQI sub-index."""
    return ((aqi_hi - aqi_lo) / (c_hi - c_lo)) * (c - c_lo) + aqi_lo


def calc_sub_aqi(concentration: float, pollutant: str) -> float:
    """
    Tính AQI sub-index cho 1 chất ô nhiễm.

    Args:
        concentration : nồng độ đo được
        pollutant     : tên chất ("pm25", "pm10", "so2", "no2", "co", "o3")

    Returns:
        AQI sub-index (float), hoặc NaN nếu ngoài bảng
    """
    if pd.isna(concentration) or concentration < 0:
        return np.nan

    breakpoints = AQI_BREAKPOINTS.get(pollutant)
    if breakpoints is None:
        return np.nan

    # CO: chuyển µg/m³ → mg/m³ (Open-Meteo trả về µg/m³)
    if pollutant == "co":
        concentration = concentration / 1000.0

    for (c_lo, c_hi, aqi_lo, aqi_hi) in breakpoints:
        if c_lo <= concentration <= c_hi:
            return _linear_interpolate(concentration,
                                       c_lo, c_hi, aqi_lo, aqi_hi)

    # Vượt ngưỡng cao nhất
    return 500.0


def calc_aqi_row(row: pd.Series) -> float:
    """
    Tính AQI tổng hợp cho 1 hàng: lấy max của các sub-index.
    Theo quy định QCVN: AQI = max(AQI_PM2.5, AQI_PM10, AQI_SO2, ...)
    """
    sub_indices = []
    for pollutant in ["pm25", "pm10", "so2", "no2", "co", "o3"]:
        if pollutant in row and pd.notna(row[pollutant]):
            sub = calc_sub_aqi(row[pollutant], pollutant)
            if not np.isnan(sub):
                sub_indices.append(sub)

    return max(sub_indices) if sub_indices else np.nan


def add_aqi_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Thêm các cột AQI vào DataFrame:
    - aqi_vn      : AQI tổng hợp theo QCVN 05:2023
    - aqi_pm25    : Sub-index PM2.5
    - aqi_pm10    : Sub-index PM10
    - aqi_so2     : Sub-index SO2
    - aqi_no2     : Sub-index NO2
    - aqi_co      : Sub-index CO
    - aqi_o3      : Sub-index O3
    - aqi_level   : Nhãn chữ (Tốt, Trung bình, ...)
    - aqi_color   : Mã màu hex (#00e400, ...)
    - dominant_pollutant : Chất gây AQI cao nhất
    """
    df = df.copy()

    pollutants = ["pm25", "pm10", "so2", "no2", "co", "o3"]

    # Tính sub-index cho từng chất
    for p in pollutants:
        if p in df.columns:
            df[f"aqi_{p}"] = df[p].apply(
                lambda x: calc_sub_aqi(x, p)
            )

    # AQI tổng hợp = max sub-index
    sub_cols = [f"aqi_{p}" for p in pollutants if f"aqi_{p}" in df.columns]
    df["aqi_vn"] = df[sub_cols].max(axis=1)

    # Dominant pollutant
    def get_dominant(row):
        vals = {p: row.get(f"aqi_{p}", np.nan) for p in pollutants}
        vals = {k: v for k, v in vals.items() if not np.isnan(v)}
        return max(vals, key=vals.get) if vals else None

    df["dominant_pollutant"] = df.apply(get_dominant, axis=1)

    # Nhãn và màu
    def get_level_label(aqi):
        if pd.isna(aqi):
            return None, None
        for lo, hi, label, color in AQI_LEVELS:
            if lo <= aqi <= hi:
                return label, color
        return "Nguy hại", "#7e0023"

    df[["aqi_level", "aqi_color"]] = df["aqi_vn"].apply(
        lambda x: pd.Series(get_level_label(x))
    )

    return df


# ── Test nhanh ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Test với giá trị mẫu
    test_cases = [
        {"pm25": 20,  "pm10": 40,  "so2": 30,  "no2": 30,  "co": 1000, "o3": 50},
        {"pm25": 80,  "pm10": 120, "so2": 100, "no2": 80,  "co": 5000, "o3": 100},
        {"pm25": 200, "pm10": 300, "so2": 400, "no2": 250, "co": 20000,"o3": 200},
    ]

    df_test = pd.DataFrame(test_cases)
    df_result = add_aqi_columns(df_test)

    print("=== Kiểm tra tính AQI theo QCVN 05:2023 ===")
    display_cols = ["pm25", "aqi_pm25", "aqi_vn", "aqi_level", "dominant_pollutant"]
    print(df_result[display_cols].to_string())