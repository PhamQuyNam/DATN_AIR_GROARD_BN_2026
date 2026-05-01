"""
app/api/routes/history.py
Endpoints tra cứu lịch sử AQI và tổng hợp thống kê.
"""
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select, func
from datetime import datetime, timedelta
from typing import Optional

from app.core.database import get_session
from app.models.db_models import AQILog, Village

router = APIRouter()


@router.get("/history/query")
def query_history(
    village: Optional[str] = Query(None, description="Tên làng nghề (bỏ trống = tất cả)"),
    start: Optional[str] = Query(None, description="Ngày bắt đầu (YYYY-MM-DD)"),
    end: Optional[str] = Query(None, description="Ngày kết thúc (YYYY-MM-DD)"),
    limit: int = Query(200, le=1000),
    session: Session = Depends(get_session)
):
    """
    Tra cứu dữ liệu AQI thô theo khoảng thời gian và làng nghề.
    Mặc định: 7 ngày gần nhất nếu không chỉ định.
    """
    query = select(AQILog).order_by(AQILog.timestamp.desc())

    # Lọc theo làng nghề
    if village:
        query = query.where(AQILog.village_name == village)

    # Lọc theo khoảng thời gian
    if start:
        try:
            start_dt = datetime.strptime(start, "%Y-%m-%d")
            query = query.where(AQILog.timestamp >= start_dt)
        except ValueError:
            pass

    if end:
        try:
            end_dt = datetime.strptime(end, "%Y-%m-%d") + timedelta(days=1)
            query = query.where(AQILog.timestamp < end_dt)
        except ValueError:
            pass

    # Nếu không có bộ lọc thời gian, mặc định 7 ngày gần nhất
    if not start and not end:
        default_start = datetime.utcnow() - timedelta(days=7)
        query = query.where(AQILog.timestamp >= default_start)

    logs = session.exec(query.limit(limit)).all()

    return {
        "count": len(logs),
        "data": [
            {
                "village_name": log.village_name,
                "timestamp": log.timestamp,
                "aqi": log.aqi,
                "level": log.level,
                "pm25": log.pm25,
                "pm10": log.pm10,
                "temperature": log.temperature,
                "humidity": log.humidity,
                "wind_speed": log.wind_speed,
            }
            for log in logs
        ]
    }


@router.get("/history/summary")
def get_summary(
    village: Optional[str] = Query(None),
    period: str = Query("week", description="'week' hoặc 'month'"),
    session: Session = Depends(get_session)
):
    """
    Tổng hợp thống kê AQI: avg, max, min theo từng ngày.
    Dùng để vẽ biểu đồ xu hướng tuần/tháng.
    """
    if period == "month":
        since = datetime.utcnow() - timedelta(days=30)
    else:
        since = datetime.utcnow() - timedelta(days=7)

    query = select(AQILog).where(AQILog.timestamp >= since)
    if village:
        query = query.where(AQILog.village_name == village)

    logs = session.exec(query.order_by(AQILog.timestamp)).all()

    # Nhóm theo ngày và tính avg/max/min
    daily = {}
    for log in logs:
        day_key = log.timestamp.strftime("%Y-%m-%d")
        if day_key not in daily:
            daily[day_key] = {"values": [], "levels": []}
        daily[day_key]["values"].append(log.aqi)
        daily[day_key]["levels"].append(log.level)

    result = []
    for day, data in sorted(daily.items()):
        vals = data["values"]
        avg_aqi = round(sum(vals) / len(vals))
        result.append({
            "date": day,
            "avg_aqi": avg_aqi,
            "max_aqi": round(max(vals)),
            "min_aqi": round(min(vals)),
            "count": len(vals),
        })

    # Tính tổng kết cả kỳ
    all_vals = [log.aqi for log in logs]
    summary_stats = {
        "period": period,
        "village": village or "Tất cả làng nghề",
        "total_records": len(logs),
        "overall_avg": round(sum(all_vals) / len(all_vals)) if all_vals else 0,
        "overall_max": round(max(all_vals)) if all_vals else 0,
        "overall_min": round(min(all_vals)) if all_vals else 0,
    }

    return {
        "summary": summary_stats,
        "daily": result
    }
