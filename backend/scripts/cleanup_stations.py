import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select, delete
from app.core.database import engine
from app.models.db_models import Village, AlertConfig, AQILog

def cleanup():
    original_18 = [
        'Đa Hội', 'Đồng Kỵ', 'Phù Khê', 'Hương Mạc', 'Đình Bảng', 
        'Văn Môn', 'Vọng Nguyệt', 'Phong Khê', 'Khắc Niệm', 'Châm Khê', 
        'Phù Lãng', 'Quả Cảm', 'Đại Bái', 'Xuân Lai', 'Môn Quảng', 
        'Đông Hồ', 'Thanh Hoài', 'Tam Tảo'
    ]
    
    with Session(engine) as session:
        villages = session.exec(select(Village)).all()
        for v in villages:
            if v.name not in original_18:
                print(f"🗑️ Đang xóa trạm phụ trợ: {v.name}")
                
                # Xóa dữ liệu liên quan để tránh lỗi Foreign Key
                session.exec(delete(AQILog).where(AQILog.village_name == v.name))
                session.exec(delete(AlertConfig).where(AlertConfig.village_name == v.name))
                from app.models.db_models import AlertHistory, UserFavoriteStation, Recommendation
                session.exec(delete(AlertHistory).where(AlertHistory.village_name == v.name))
                session.exec(delete(UserFavoriteStation).where(UserFavoriteStation.village_name == v.name))
                session.exec(delete(Recommendation).where(Recommendation.village_name == v.name))
                
                session.delete(v)
                
        session.commit()
    print("✅ Đã dọn dẹp xong, hệ thống hiện chỉ còn 18 trạm gốc.")

if __name__ == "__main__":
    cleanup()
