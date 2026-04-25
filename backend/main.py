import sys
import os
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session

# Thêm đường dẫn để có thể import từ app
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import init_db, get_session
from app.models.db_models import Village, AQILog
from app.scheduler.jobs import start_scheduler

app = FastAPI(
    title="AirGuard BN API",
    description="API for Air Quality Monitoring and Forecast System",
    version="1.0.0"
)

# Cấu hình CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()
    start_scheduler()

from app.api.routes import aqi, forecast, shap, alert, analytics

app.include_router(aqi.router, prefix="/api/v1", tags=["AQI"])
app.include_router(forecast.router, prefix="/api/v1", tags=["Forecast"])
app.include_router(shap.router, prefix="/api/v1", tags=["SHAP"])
app.include_router(alert.router, prefix="/api/v1/alerts", tags=["Alerts"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["Analytics"])

@app.get("/")
def read_root():
    return {"message": "Welcome to AirGuard BN API"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
