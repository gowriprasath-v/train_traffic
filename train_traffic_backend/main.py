# main.py
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from models import ScheduleRequest, Alert
from database_pg import save_schedule_to_db, get_schedule_from_db
from mongo_alerts import save_alert, get_recent_alerts
from ai_model import get_optimized_schedule, compute_metrics
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Train Traffic Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for dev; lock this down for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"msg": "Backend running"}

@app.post("/api/v1/optimize")
def optimize(data: ScheduleRequest):
    """
    Optimize the incoming schedule and persist the result.
    Returns the optimized schedule.
    """
    logger.info(f"/optimize called with {len(data.trains)} trains for date {data.date}")
    if not data.trains:
        raise HTTPException(status_code=400, detail="No trains provided")

    optimized = get_optimized_schedule(data)
    try:
        save_schedule_to_db(optimized)
    except Exception as e:
        logger.exception("Failed to save optimized schedule to DB")
        raise HTTPException(status_code=500, detail="Failed to persist schedule")

    return {"schedule": optimized}

@app.get("/api/v1/schedule")
def get_schedule():
    logger.info("/schedule GET called")
    try:
        schedule = get_schedule_from_db()
    except Exception:
        raise HTTPException(status_code=500, detail="Error reading schedule from DB")
    if not schedule:
        raise HTTPException(status_code=404, detail="No schedule found")
    return {"schedule": schedule}

@app.get("/api/v1/metrics")
def get_metrics():
    """
    Compute station-level metrics from the stored schedule and return them.
    """
    try:
        schedule = get_schedule_from_db()
    except Exception:
        raise HTTPException(status_code=500, detail="Error reading schedule from DB")
    if not schedule:
        return {"metrics": {}}
    metrics = compute_metrics(schedule)
    return {"metrics": metrics}

@app.post("/api/v1/alerts")
def post_alert(alert: Alert):
    logger.info("Received alert")
    try:
        save_alert(alert.model_dump())
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to store alert")
    return {"status": "alert saved"}

@app.get("/api/v1/alerts")
def recent_alerts():
    try:
        alerts = get_recent_alerts(10)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to read alerts")
    return {"alerts": alerts}

@app.get("/health")
def health_check():
    return {"status": "ok"}
