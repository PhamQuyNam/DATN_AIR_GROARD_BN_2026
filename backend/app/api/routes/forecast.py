from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from typing import List

from app.core.database import get_session
from app.models.db_models import Village, ForecastLog

router = APIRouter()

@router.get("/forecast/current")
def get_current_forecast_all(session: Session = Depends(get_session)):
    """
    Lấy dự báo 6h tới cho tất cả các làng nghề.
    """
    villages = session.exec(select(Village)).all()
    results = []
    
    for v in villages:
        forecasts = session.exec(
            select(ForecastLog)
            .where(ForecastLog.village_name == v.name)
            .order_by(ForecastLog.forecast_hour.asc())
        ).all()
        
        if forecasts:
            results.append({
                "village_name": v.name,
                "forecasts": forecasts
            })
            
    return {"data": results}

@router.get("/forecast/{village_name}")
def get_village_forecast(village_name: str, session: Session = Depends(get_session)):
    """
    Lấy dự báo 6h tới cho một làng nghề cụ thể (kèm khoảng tin cậy).
    """
    village = session.exec(select(Village).where(Village.name == village_name)).first()
    if not village:
        raise HTTPException(status_code=404, detail="Village not found")
        
    forecasts = session.exec(
        select(ForecastLog)
        .where(ForecastLog.village_name == village_name)
        .order_by(ForecastLog.forecast_hour.asc())
    ).all()
    
    return {"village_name": village_name, "forecasts": forecasts}

@router.post("/forecast/run_inference_now")
def run_inference_now():
    """
    Kích hoạt chạy AI (LSTM & XGBoost) ngay lập tức thay vì đợi scheduler.
    Phục vụ cho mục đích Test hiển thị giao diện.
    """
    from app.services.inference_service import inference_service
    inference_service.run_forecast_all()
    return {"status": "success", "message": "Đã chạy xong mô hình dự báo AI"}
