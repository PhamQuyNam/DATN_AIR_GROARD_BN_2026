from apscheduler.schedulers.background import BackgroundScheduler
from app.services.collector_service import AQICollector
from app.services.inference_service import inference_service
from app.services.alert_service import check_and_create_alerts

scheduler = BackgroundScheduler()

def scheduled_update_job():
    print("⏰ Starting scheduled update job...")
    # 1. Thu thập dữ liệu từ Internet
    AQICollector.fetch_live_data()
    
    # 2. Chạy model dự báo
    inference_service.run_forecast_all()
    
    # 3. Kiểm tra ngưỡng và tạo cảnh báo nếu cần
    check_and_create_alerts()
    print("⏰ Scheduled update job finished.")

def start_scheduler():
    # Thiết lập chạy định kỳ mỗi 5 phút
    scheduler.add_job(scheduled_update_job, 'interval', minutes=5)
    scheduler.start()
    print("🚀 Scheduler started. Jobs scheduled every 5 minutes.")
