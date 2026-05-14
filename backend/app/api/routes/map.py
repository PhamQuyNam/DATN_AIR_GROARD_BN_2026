"""
app/api/routes/map.py
Endpoints: Trạng thái Online/Offline của các trạm quan trắc.
"""
from fastapi import APIRouter, Depends
from sqlmodel import Session, select
from datetime import datetime, timedelta

from app.core.database import get_session
from app.models.db_models import Village, AQILog

router = APIRouter()

# Ngưỡng: Bản ghi mới hơn 2 giờ → Online, lâu hơn → Offline
OFFLINE_THRESHOLD_HOURS = 2

@router.get("/map/status")
def get_station_status(session: Session = Depends(get_session)):
    """
    Lấy danh sách trạng thái Online/Offline cho tất cả làng nghề.
    Dựa trên thời gian của bản ghi AQILog mới nhất của từng làng.
    """
    villages = session.exec(select(Village)).all()
    now = datetime.utcnow()
    cutoff = now - timedelta(hours=OFFLINE_THRESHOLD_HOURS)

    results = []
    online_count = 0
    offline_count = 0

    for v in villages:
        latest = session.exec(
            select(AQILog)
            .where(AQILog.village_name == v.name)
            .order_by(AQILog.timestamp.desc())
            .limit(1)
        ).first()

        if latest and v.is_active:
            # Chỉ Online khi được Admin BẬT và có dữ liệu mới
            is_online = latest.timestamp >= cutoff
            last_seen = latest.timestamp
            current_aqi = latest.aqi
            current_level = latest.level
        else:
            is_online = False
            last_seen = latest.timestamp if latest else None
            current_aqi = latest.aqi if latest else None
            current_level = latest.level if latest else "Không có dữ liệu"

        status = "ONLINE" if is_online else "OFFLINE"
        if is_online:
            online_count += 1
        else:
            offline_count += 1

        # Tính thời gian trôi qua từ lần cập nhật cuối
        if last_seen:
            delta = now - last_seen
            hours_ago = int(delta.total_seconds() // 3600)
            mins_ago = int((delta.total_seconds() % 3600) // 60)
            if hours_ago > 0:
                time_ago_str = f"{hours_ago}h {mins_ago}m trước"
            else:
                time_ago_str = f"{mins_ago} phút trước"
        else:
            time_ago_str = "Chưa có dữ liệu"

        results.append({
            "village_name": v.name,
            "location": v.location,
            "lat": v.lat,
            "lon": v.lon,
            "status": status,
            "is_online": is_online,
            "is_active": v.is_active,  # Trạng thái admin bật/tắt
            "current_aqi": current_aqi,
            "current_level": current_level,
            "last_seen": last_seen,
            "time_ago": time_ago_str,
        })

    # Sắp xếp: Offline lên đầu để dễ phát hiện vấn đề
    results.sort(key=lambda x: (x["is_online"], x["village_name"]))

    return {
        "total": len(results),
        "online_count": online_count,
        "offline_count": offline_count,
        "stations": results
    }
