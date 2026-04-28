from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from datetime import datetime, timedelta

from app.core.database import get_session
from app.models.db_models import Village, AQILog

router = APIRouter()

@router.get("/villages", response_model=List[Village])
def get_villages(session: Session = Depends(get_session)):
    """Lấy danh sách 18 làng nghề kèm thông tin cơ bản"""
    return session.exec(select(Village)).all()

@router.get("/aqi/current")
def get_current_aqi_all_villages(session: Session = Depends(get_session)):
    """
    Lấy thông số AQI và nồng độ các chất MỚI NHẤT của toàn bộ 18 làng nghề.
    Dùng để vẽ các chấm màu trên bản đồ thời gian thực.
    """
    villages = session.exec(select(Village)).all()
    results = []
    
    for v in villages:
        latest = session.exec(
            select(AQILog)
            .where(AQILog.village_name == v.name)
            .order_by(AQILog.timestamp.desc())
            .limit(1)
        ).first()
        
        if latest:
            results.append({
                "village_name": v.name,
                "lat": v.lat,
                "lon": v.lon,
                "timestamp": latest.timestamp,
                "aqi": latest.aqi,
                "level": latest.level,
                "pm25": latest.pm25,
                "co": latest.co,
                "no2": latest.no2,
                "so2": latest.so2,
                "o3": latest.o3
            })
    return {"data": results}

@router.get("/aqi/history/{village_name}")
def get_aqi_history(village_name: str, limit: int = 24, session: Session = Depends(get_session)):
    """
    Lấy dữ liệu AQI lịch sử của một làng nghề (mặc định 24 bản ghi gần nhất).
    Dùng để vẽ biểu đồ đường (Line chart) liên tục với dự báo.
    """
    # Kiểm tra xem làng nghề có tồn tại không
    village = session.exec(select(Village).where(Village.name == village_name)).first()
    if not village:
        raise HTTPException(status_code=404, detail="Village not found")
        
    logs = session.exec(
        select(AQILog)
        .where(AQILog.village_name == village_name)
        .order_by(AQILog.timestamp.desc())
        .limit(limit)
    ).all()
    
    logs.reverse() # Đảo ngược để dữ liệu vẽ từ trái qua phải (cũ -> mới)
    return {"village": village_name, "data": logs}
    
    return {"village": village_name, "data": logs}
