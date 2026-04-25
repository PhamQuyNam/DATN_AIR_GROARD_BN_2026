from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from typing import List, Optional
from datetime import datetime, timedelta

from app.core.database import get_session
from app.models.db_models import Village, AQILog

router = APIRouter()

@router.get("/trends")
def get_analytics_trends(
    villages: Optional[List[str]] = Query(None),
    timeframe: str = Query("day", description="Khung thời gian: hour, day, week, month"),
    session: Session = Depends(get_session)
):
    """
    Phân tích xu hướng chất lượng không khí.
    Dùng để vẽ biểu đồ so sánh giữa các làng nghề.
    """
    # Để đơn giản hóa trong phiên bản này, ta sẽ trả về raw data của các làng nghề
    # được chọn trong khoảng thời gian tương ứng.
    # Trong môi trường production, bạn sẽ dùng Group By và Avg() của SQL.
    
    days_map = {"hour": 1, "day": 1, "week": 7, "month": 30}
    days = days_map.get(timeframe, 7)
    
    start_date = datetime.now() - timedelta(days=days)
    
    query = select(AQILog).where(AQILog.timestamp >= start_date)
    
    if villages:
        query = query.where(AQILog.village_name.in_(villages))
        
    query = query.order_by(AQILog.timestamp.asc())
    
    logs = session.exec(query).all()
    
    return {"timeframe": timeframe, "data": logs}
