from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from models import ScheduleRequest, Alert
from database_pg import save_schedule_to_db, get_schedule_from_db
from mongo_alerts import save_alert, get_recent_alerts
from sqlalchemy.exc import SQLAlchemyError
from pymongo.errors import PyMongoError
from ai_model import compute_metrics, predict_delays
from scheduler import get_optimized_schedule
import logging
import json
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Train Traffic Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        disconnected_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except WebSocketDisconnect:
                disconnected_connections.append(connection)
            except Exception as e:
                logger.error(f"Error sending message to WebSocket: {e}")
                disconnected_connections.append(connection)
        for conn in disconnected_connections:
            self.active_connections.remove(conn)

manager = ConnectionManager()

def check_for_overlaps(trains):
    fmt = "%H:%M"
    by_platform = {}
    for t in trains:
        by_platform.setdefault(t.platform, []).append(t)

    for platform, trains_on_platform in by_platform.items():
        sorted_trains = sorted(trains_on_platform, key=lambda x: datetime.strptime(x.arrival, fmt))
        for i in range(len(sorted_trains) - 1):
            current_train = sorted_trains[i]
            next_train = sorted_trains[i+1]
            current_departure = datetime.strptime(current_train.departure, fmt)
            next_arrival = datetime.strptime(next_train.arrival, fmt)
            if current_departure > next_arrival:
                raise HTTPException(
                    status_code=400,
                    detail=f"Overlap detected on platform {platform} between trains {current_train.train_id} and {next_train.train_id}"
                )

@app.get("/")
def root():
    return {"msg": "Backend running"}

@app.post("/api/v1/optimize")
async def optimize(data: ScheduleRequest):
    logger.info(f"/optimize called with {len(data.trains)} trains for date {data.date}")
    if not data.trains:
        raise HTTPException(status_code=400, detail="No trains provided")
    
    check_for_overlaps(data.trains)
    
    trains_with_predictions = predict_delays(data.trains)
    data.trains = trains_with_predictions
    optimized = get_optimized_schedule(data)
    
    
    try:
        save_schedule_to_db(optimized)
    except SQLAlchemyError:
        logger.exception("Failed to save optimized schedule to DB")
        raise HTTPException(status_code=500, detail="A database error occurred while saving the schedule.")
    
    metrics = compute_metrics(optimized)
    await manager.broadcast(json.dumps({"type": "metrics_update", "metrics": metrics}))
    return {"schedule": optimized}

@app.get("/api/v1/schedule")
def get_schedule():
    logger.info("/schedule GET called")
    try:
        schedule = get_schedule_from_db()
    except SQLAlchemyError:
        logger.exception("Error reading schedule from DB")
        raise HTTPException(status_code=500, detail="A database error occurred while reading the schedule.")
    if not schedule:
        raise HTTPException(status_code=404, detail="No schedule found")
    return {"schedule": schedule}

    try:
        schedule = get_schedule_from_db()
    except SQLAlchemyError:
        logger.exception("Error reading schedule from DB for metrics")
        raise HTTPException(status_code=500, detail="A database error occurred while reading the schedule for metrics.")
    if not schedule:
        return {"metrics": {}}
    metrics = compute_metrics(schedule)
    return {"metrics": metrics}

@app.post("/api/v1/alerts")
def post_alert(alert: Alert):
    logger.info("Received alert")
    try:
        save_alert(alert.model_dump())
    except PyMongoError:
        logger.exception("Failed to store alert in MongoDB")
        raise HTTPException(status_code=500, detail="A database error occurred while storing the alert.")
    return {"status": "alert saved"}

@app.get("/api/v1/alerts")
def recent_alerts():
    try:
        alerts = get_recent_alerts(10)
    except PyMongoError:
        logger.exception("Failed to read alerts from MongoDB")
        raise HTTPException(status_code=500, detail="A database error occurred while reading alerts.")
    return {"alerts": alerts}

@app.websocket("/ws/metrics")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)

@app.get("/health")
def health_check():
    return {"status": "ok"}
