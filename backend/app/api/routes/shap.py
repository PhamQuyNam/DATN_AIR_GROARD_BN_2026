from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select

from app.core.database import get_session
from app.models.db_models import Village, AQILog

router = APIRouter()

@router.get("/shap/{village_name}")
def get_shap_values(village_name: str, session: Session = Depends(get_session)):
    """
    Lấy giá trị SHAP (Mức độ ảnh hưởng của các yếu tố) mới nhất của một làng nghề.
    Dùng để hiển thị biểu đồ phân tích nguyên nhân ô nhiễm.
    """
    village = session.exec(select(Village).where(Village.name == village_name)).first()
    if not village:
        raise HTTPException(status_code=404, detail="Village not found")
        
    latest_log = session.exec(
        select(AQILog)
        .where(AQILog.village_name == village_name)
        .order_by(AQILog.timestamp.desc())
        .limit(1)
    ).first()
    
    if not latest_log or not latest_log.shap_values:
        return {"village_name": village_name, "timestamp": None, "shap_values": {}}
        
    return {
        "village_name": village_name,
        "timestamp": latest_log.timestamp,
        "shap_values": latest_log.shap_values
    }
