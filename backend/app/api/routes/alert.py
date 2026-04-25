from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from pydantic import BaseModel

from app.core.database import get_session
from app.models.db_models import Village, AlertConfig, AlertHistory

router = APIRouter()

class AlertConfigUpdate(BaseModel):
    aqi_threshold: float
    is_active: bool

@router.get("/active")
def get_active_alerts(session: Session = Depends(get_session)):
    """
    Lấy danh sách các cảnh báo ĐANG HIỆU LỰC (AQI hiện tại vượt ngưỡng).
    (Trong thực tế, bạn sẽ join bảng AQILog mới nhất và AlertConfig để so sánh. 
    Ở đây ta tạm query từ bảng AlertHistory những cảnh báo của ngày hôm nay).
    """
    # Lấy 10 cảnh báo gần nhất
    alerts = session.exec(
        select(AlertHistory)
        .order_by(AlertHistory.timestamp.desc())
        .limit(10)
    ).all()
    return {"data": alerts}

@router.get("/config", response_model=List[AlertConfig])
def get_alert_configs(session: Session = Depends(get_session)):
    """
    Lấy danh sách cấu hình cảnh báo của tất cả làng nghề.
    """
    configs = session.exec(select(AlertConfig)).all()
    return configs

@router.post("/config/{village_name}")
def update_alert_config(
    village_name: str, 
    config_update: AlertConfigUpdate,
    session: Session = Depends(get_session)
):
    """
    Admin: Cập nhật ngưỡng cảnh báo cho một làng nghề cụ thể.
    """
    config = session.exec(select(AlertConfig).where(AlertConfig.village_name == village_name)).first()
    
    if not config:
        # Nếu chưa có cấu hình, tạo mới
        village = session.exec(select(Village).where(Village.name == village_name)).first()
        if not village:
            raise HTTPException(status_code=404, detail="Village not found")
            
        config = AlertConfig(
            village_name=village_name,
            aqi_threshold=config_update.aqi_threshold,
            is_active=config_update.is_active
        )
        session.add(config)
    else:
        config.aqi_threshold = config_update.aqi_threshold
        config.is_active = config_update.is_active
        
    session.commit()
    session.refresh(config)
    
    return {"message": "Config updated successfully", "data": config}
