"""
Seed SHAP values vào bản ghi AQILog mới nhất của mỗi làng nghề.
SHAP values mô phỏng mức độ đóng góp của từng yếu tố vào chỉ số AQI.
"""
import sys, os, random, json
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.database import engine
from app.models.db_models import Village, AQILog
from sqlmodel import Session, select

def generate_shap(log: AQILog) -> dict:
    """Sinh SHAP values thực tế dựa trên giá trị của chính bản ghi."""
    pm25    = log.pm25 or 50
    pm10    = log.pm10 or 60
    no2     = log.no2  or 15
    so2     = log.so2  or 10
    o3      = log.o3   or 20
    co      = log.co   or 1
    wind    = log.wind_speed or 2
    temp    = log.temperature or 28
    hum     = log.humidity or 70

    # PM2.5 đóng góp lớn nhất và luôn dương (làm AQI xấu hơn)
    shap_pm25    = round(pm25 * random.uniform(0.30, 0.45), 2)
    shap_pm10    = round(pm10 * random.uniform(0.08, 0.15), 2)
    shap_no2     = round(no2  * random.uniform(0.05, 0.12), 2)
    shap_so2     = round(so2  * random.uniform(0.03, 0.08), 2)
    shap_o3      = round(o3   * random.uniform(0.02, 0.07), 2)
    shap_co      = round(co   * random.uniform(2.0,  5.0),  2)
    # Gió và độ ẩm cao → pha loãng ô nhiễm → giá trị âm
    shap_wind    = round(-wind * random.uniform(1.5, 4.0),  2)
    shap_temp    = round((temp - 25) * random.uniform(0.3, 0.9), 2)  # nhiệt độ cao → xấu hơn
    shap_hum     = round(-(hum - 60) * random.uniform(0.1, 0.3), 2)  # độ ẩm cao → pha loãng

    return {
        "pm25":        shap_pm25,
        "pm10":        shap_pm10,
        "no2":         shap_no2,
        "so2":         shap_so2,
        "o3":          shap_o3,
        "co":          shap_co,
        "wind_speed":  shap_wind,
        "temperature": round(shap_temp, 2),
        "humidity":    round(shap_hum, 2),
    }

def seed_shap():
    with Session(engine) as session:
        villages = session.exec(select(Village)).all()
        updated = 0

        for village in villages:
            # Lấy 5 bản ghi mới nhất để có biểu đồ phong phú hơn
            logs = session.exec(
                select(AQILog)
                .where(AQILog.village_name == village.name)
                .order_by(AQILog.timestamp.desc())
                .limit(5)
            ).all()

            for log in logs:
                log.shap_values = generate_shap(log)
                session.add(log)
                updated += 1

        session.commit()
        print(f"✅ Đã seed SHAP values cho {updated} bản ghi AQILog của {len(villages)} làng nghề")

if __name__ == "__main__":
    print("🚀 Bắt đầu seed SHAP values...")
    seed_shap()
    print("🎉 Hoàn tất!")
