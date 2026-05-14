from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List
from pydantic import BaseModel
from datetime import datetime

from app.core.database import get_session
from app.models.db_models import Village, AlertConfig, AlertHistory, Recommendation, User
from app.api.routes.auth import get_current_manager

router = APIRouter()

class AlertConfigUpdate(BaseModel):
    aqi_threshold: float
    is_active: bool

class AlertConfigResponse(BaseModel):
    village_name: str
    aqi_threshold: float
    is_active: bool
    village_active: bool

class RecommendationCreate(BaseModel):
    village_name: str
    content: str

@router.post("/approve/{alert_id}", status_code=200)
def approve_alert(
    alert_id: int,
    session: Session = Depends(get_session),
    current_manager: User = Depends(get_current_manager)
):
    """
    MANAGER phê duyệt một cảnh báo → đánh dấu is_approved=True.
    Cảnh báo đã duyệt sẽ xuất hiện trong tab 'Cảnh báo' phía người dân
    (không tạo Recommendation — đó là chức năng riêng biệt).
    """
    alert = session.get(AlertHistory, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Không tìm thấy cảnh báo")

    if alert.is_approved:
        return {"message": "Cảnh báo này đã được phê duyệt trước đó"}

    # Chỉ đánh dấu đã duyệt
    alert.is_approved = True
    alert.approved_by = current_manager.id
    alert.approved_at = datetime.utcnow()
    session.add(alert)
    session.commit()

    return {
        "message": f"✅ Đã phê duyệt cảnh báo tại {alert.village_name}. Người dân theo dõi trạm này sẽ nhận được thông báo.",
        "village": alert.village_name,
        "aqi_value": alert.aqi_value
    }


@router.delete("/{alert_id}", status_code=200)
def delete_alert(
    alert_id: int,
    session: Session = Depends(get_session),
    current_manager: User = Depends(get_current_manager)
):
    """MANAGER: Xóa một bản ghi cảnh báo khỏi hệ thống."""
    alert = session.get(AlertHistory, alert_id)
    if not alert:
        raise HTTPException(status_code=404, detail="Không tìm thấy cảnh báo")
    session.delete(alert)
    session.commit()
    return {"message": f"Đã xóa cảnh báo tại {alert.village_name}"}


@router.get("/recommend/{village_name}")
def get_recommendation(village_name: str, session: Session = Depends(get_session)):
    """Lấy khuyến nghị sức khỏe mới nhất cho một làng nghề (public)."""
    rec = session.exec(
        select(Recommendation)
        .where(Recommendation.village_name == village_name)
        .where(Recommendation.is_active == True)
        .order_by(Recommendation.created_at.desc())
        .limit(1)
    ).first()
    if not rec:
        return {"data": None}
    return {"data": rec}

@router.post("/recommend", status_code=201)
def create_recommendation(
    req: RecommendationCreate,
    session: Session = Depends(get_session),
    current_manager: User = Depends(get_current_manager)
):
    """MANAGER: Soạn và gửi khuyến nghị sức khỏe đến một làng nghề."""
    village = session.exec(select(Village).where(Village.name == req.village_name)).first()
    if not village:
        raise HTTPException(status_code=404, detail="Không tìm thấy làng nghề")

    rec = Recommendation(
        manager_id=current_manager.id,
        village_name=req.village_name,
        content=req.content,
        is_active=True
    )
    session.add(rec)
    session.commit()
    session.refresh(rec)
    return {"message": "Đã gửi khuyến nghị thành công", "data": rec}

@router.get("/recommend")
def get_all_recommendations(session: Session = Depends(get_session)):
    """Lấy danh sách tất cả khuyến nghị gần đây (public)."""
    recs = session.exec(
        select(Recommendation)
        .where(Recommendation.is_active == True)
        .order_by(Recommendation.created_at.desc())
        .limit(50)
    ).all()
    return {"data": recs}



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

@router.get("/config", response_model=List[AlertConfigResponse])
def get_alert_configs(session: Session = Depends(get_session)):
    """
    Lấy danh sách cấu hình cảnh báo kèm trạng thái hoạt động của làng nghề.
    """
    # Join AlertConfig với Village để lấy trạng thái đồng bộ
    results = session.exec(
        select(AlertConfig, Village.is_active)
        .join(Village, AlertConfig.village_name == Village.name)
    ).all()
    
    return [
        AlertConfigResponse(
            village_name=conf.village_name,
            aqi_threshold=conf.aqi_threshold,
            is_active=conf.is_active,
            village_active=v_active
        ) for conf, v_active in results
    ]

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
        # Đồng bộ trạng thái sang Village
        village.is_active = config_update.is_active
        session.add(config)
        session.add(village)
    else:
        config.aqi_threshold = config_update.aqi_threshold
        config.is_active = config_update.is_active
        
        # Đồng bộ trạng thái sang Village tương ứng
        village = session.exec(select(Village).where(Village.name == village_name)).first()
        if village:
            village.is_active = config_update.is_active
            session.add(village)
            
    session.commit()
    session.refresh(config)
    
    return {"message": "Config updated successfully", "data": config}
