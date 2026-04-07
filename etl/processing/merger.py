import pandas as pd


def merge_air_and_weather(df_air: pd.DataFrame,
                          df_weather: pd.DataFrame) -> pd.DataFrame:
    """
    Ghép dữ liệu air quality + thời tiết theo timestamp + village.
    Cả 2 nguồn đều từ Open-Meteo nên timestamp đã đồng bộ sẵn.
    """
    df_air["timestamp"]     = pd.to_datetime(df_air["timestamp"])
    df_weather["timestamp"] = pd.to_datetime(df_weather["timestamp"])

    # Làm tròn về giờ để đảm bảo khớp
    df_air["timestamp"]     = df_air["timestamp"].dt.floor("h")
    df_weather["timestamp"] = df_weather["timestamp"].dt.floor("h")

    weather_cols = [
        "timestamp", "village",
        "temperature", "humidity", "wind_speed", "wind_dir",
        "precipitation", "pressure", "cloud_cover"
    ]
    weather_cols = [c for c in weather_cols if c in df_weather.columns]

    merged = pd.merge(
        df_air,
        df_weather[weather_cols],
        on=["timestamp", "village"],
        how="left"
    )

    # Sắp xếp cột theo thứ tự hợp lý cho ML
    priority_cols = [
        "timestamp", "village", "lat", "lon",
        "pm25", "pm10", "so2", "no2", "co", "o3",
        "aqi_eu", "us_aqi",
        "temperature", "humidity", "wind_speed", "wind_dir",
        "precipitation", "pressure", "cloud_cover",
        "aod", "dust", "is_forecast", "source"
    ]
    final_cols = [c for c in priority_cols if c in merged.columns]
    return merged[final_cols]