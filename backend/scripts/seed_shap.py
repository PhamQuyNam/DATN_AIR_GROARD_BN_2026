import os
import sys
import random
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlmodel import Session, select
from app.core.database import engine
from app.models.db_models import AQILog

def seed_shap():
    with Session(engine) as session:
        # Lấy bản ghi mới nhất của mỗi làng nghề
        from app.models.db_models import Village
        villages = session.exec(select(Village)).all()
        
        for v in villages:
            log = session.exec(
                select(AQILog)
                .where(AQILog.village_name == v.name)
                .order_by(AQILog.timestamp.desc())
                .limit(1)
            ).first()
            
            if log:
                # Giả lập giá trị SHAP
                log.shap_values = {
                    'Bụi mịn (PM2.5)': random.uniform(30, 50),
                    'Khí thải (CO/SO2)': random.uniform(10, 25),
                    'Nhiệt độ': random.uniform(-10, 5),
                    'Độ ẩm': random.uniform(-5, 10),
                    'Hướng gió': random.uniform(-15, -5),
                    'Mật độ sản xuất': random.uniform(5, 15)
                }
                session.add(log)
                print(f"📊 Đã nạp SHAP cho trạm: {v.name}")
        
        session.commit()
    print("✅ Hoàn tất nạp dữ liệu phân tích SHAP!")

if __name__ == "__main__":
    seed_shap()
