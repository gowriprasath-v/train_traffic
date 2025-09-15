from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from models import ScheduleRequest, Alert, SimulationRequest
from database_pg import save_schedule_to_db, get_schedule_from_db, sort_trains_by_arrival, get_db
from mongo_alerts import save_alert, get_recent_alerts
from ai_model import compute_metrics, predict_delays, generate_delay_explanation
from scheduler import get_optimized_schedule
import logging
import json
import copy
from typing import List, Optional
from datetime import datetime
import uuid

# ----------------- DIGITAL TWIN STATE -----------------
from threading import Lock

digital_twin_state = {
    "schedule": None,
    "alerts": []
}
state_lock = Lock()
# ------------------------------------------------------

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI-Powered Train Traffic Control System",
    description="Intelligent decision-support system for railway traffic optimization",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8080", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.connection_ids: dict = {}

    async def connect(self, websocket: WebSocket, client_id: str = None):
        await websocket.accept()
        if client_id is None:
            client_id = str(uuid.uuid4())
        self.active_connections.append(websocket)
        self.connection_ids[websocket] = client_id
        logger.info(f"WebSocket connected: {client_id}. Total connections: {len(self.active_connections)}")
        return client_id

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            client_id = self.connection_ids.pop(websocket, "unknown")
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected: {client_id}. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        if not self.active_connections:
            return
        disconnected_connections = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error sending message to WebSocket {self.connection_ids.get(connection, 'unknown')}: {e}")
                disconnected_connections.append(connection)
        for conn in disconnected_connections:
            self.disconnect(conn)

manager = ConnectionManager()

def check_for_overlaps(trains):
    fmt = "%H:%M"
    by_platform = {}
    for t in trains:
        platform = t.platform
        by_platform.setdefault(platform, []).append(t)
    conflicts = []
    for platform, trains_on_platform in by_platform.items():
        sorted_trains = sorted(trains_on_platform, key=lambda x: datetime.strptime(x.arrival, fmt))
        for i in range(len(sorted_trains) - 1):
            current_train = sorted_trains[i]
            next_train = sorted_trains[i+1]
            try:
                current_departure = datetime.strptime(current_train.departure, fmt)
                next_arrival = datetime.strptime(next_train.arrival, fmt)
                if current_departure > next_arrival:
                    conflicts.append({
                        "platform": platform,
                        "train1": current_train.train_id,
                        "train2": next_train.train_id,
                        "train1_departure": current_train.departure,
                        "train2_arrival": next_train.arrival
                    })
            except ValueError as e:
                logger.error(f"Time parsing error for trains on platform {platform}: {e}")
    if conflicts:
        conflict_details = "; ".join([
            f"Platform {c['platform']}: {c['train1']} (departs {c['train1_departure']}) "
            f"conflicts with {c['train2']} (arrives {c['train2_arrival']})"
            for c in conflicts
        ])
        raise HTTPException(
            status_code=400,
            detail=f"Schedule conflicts detected: {conflict_details}"
        )

@app.get("/")
def root():
    return {
        "message": "AI-Powered Train Traffic Control System",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "optimize": "/api/v1/optimize",
            "schedule": "/api/v1/schedule",
            "metrics": "/api/v1/metrics",
            "simulate": "/api/v1/simulate",
            "digital_twin_update": "/api/v1/digital_twin/update",
            "digital_twin_state": "/api/v1/digital_twin/state",
            "alerts": "/api/v1/alerts",
            "health": "/health"
        }
    }

@app.post("/api/v1/optimize")
async def optimize(
    data: ScheduleRequest,
    db=Depends(get_db),
    use_ai: bool = Query(True, description="If true, AI predicts delay/status; if false, use provided values."),
):
    logger.info(f"Optimization requested: {len(data.trains)} trains for {data.date} (use_ai={use_ai})")
    if not data.trains:
        raise HTTPException(status_code=400, detail="No trains provided")
    check_for_overlaps(data.trains)
    if use_ai:
        data.trains = predict_delays(data.trains)
    optimized = get_optimized_schedule(data)
    if not optimized or "trains" not in optimized:
        raise HTTPException(status_code=500, detail="Optimization failed")
    optimized["trains"] = sort_trains_by_arrival(optimized["trains"])
    for train in optimized["trains"]:
        if "delay_minutes" in train:
            explanation = generate_delay_explanation(
                type('Train', (), train)(),
                train["delay_minutes"]
            )
            train["explanation"] = explanation
    try:
        save_schedule_to_db(optimized, db)
    except Exception as e:
        logger.exception("Failed to save optimized schedule to DB")
        raise HTTPException(status_code=500, detail=f"Database save failed: {str(e)}")
    metrics = compute_metrics(optimized)
    await manager.broadcast(json.dumps({
        "type": "schedule_updated",
        "schedule": optimized,
        "metrics": metrics,
        "timestamp": datetime.now().isoformat()
    }))
    return {
        "schedule": optimized,
        "metrics": metrics,
        "optimization_info": {
            "total_trains": len(optimized["trains"]),
            "ai_predictions_applied": use_ai,
            "constraint_optimization": True
        }
    }

# ----------------------------------------------------------------
# DIGITAL TWIN: Update endpoint
@app.post("/api/v1/digital_twin/update")
async def update_digital_twin(data: ScheduleRequest, db=Depends(get_db)):
    with state_lock:
        digital_twin_state["schedule"] = data.dict()
        # Always enrich with delays (AI) for the digital twin view
        digital_twin_state["schedule"]["trains"] = [t.model_dump() if hasattr(t, 'model_dump') else dict(t) for t in predict_delays(data.trains)]
    # Always recalc metrics for the digital twin as well
    metrics = compute_metrics(digital_twin_state["schedule"])
    await manager.broadcast(json.dumps({
        "type": "digital_twin_update",
        "metrics": metrics,
        "schedule": digital_twin_state["schedule"]
    }))
    return {"status": "digital twin updated"}

# DIGITAL TWIN: Return current in-memory state (schedule + alerts)
@app.get("/api/v1/digital_twin/state")
def get_digital_twin_state():
    with state_lock:
        if digital_twin_state["schedule"]:
            return digital_twin_state
        else:
            raise HTTPException(status_code=404, detail="Digital twin state not available")        
# ----------------------------------------------------------------

@app.get("/api/v1/schedule")
def get_schedule(db=Depends(get_db), include_explanations: bool = Query(False)):
    logger.info("Schedule retrieval requested")
    schedule = get_schedule_from_db(db)
    if not schedule:
        raise HTTPException(status_code=404, detail="No schedule found")
    if include_explanations:
        for train in schedule.get("trains", []):
            if "delay_minutes" in train:
                explanation = generate_delay_explanation(
                    type('Train', (), train)(),
                    train["delay_minutes"]
                )
                train["explanation"] = explanation
    return {"schedule": schedule}

@app.get("/api/v1/metrics")
def get_metrics(db=Depends(get_db)):
    schedule = get_schedule_from_db(db)
    if not schedule:
        return {"metrics": {}}
    metrics = compute_metrics(schedule)
    return {
        "metrics": metrics,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/simulate")
async def simulate_scenario(simulation: SimulationRequest, db=Depends(get_db)):
    logger.info(f"Simulation requested with {len(simulation.disruptions)} disruptions")
    sim_schedule = copy.deepcopy(simulation.schedule)
    for disruption in simulation.disruptions:
        train_id = disruption.get("train_id")
        disruption_type = disruption.get("type")
        for train in sim_schedule.trains:
            if train.train_id == train_id:
                if disruption_type == "delay":
                    additional_delay = disruption.get("delay_minutes", 0)
                    train.delay_minutes = (train.delay_minutes or 0) + additional_delay
                elif disruption_type == "platform_change":
                    new_platform = disruption.get("new_platform")
                    if new_platform:
                        train.platform = new_platform
                elif disruption_type == "cancellation":
                    train.status = "cancelled"
                break
    optimized_sim = get_optimized_schedule(sim_schedule)
    optimized_sim["trains"] = sort_trains_by_arrival(optimized_sim["trains"])
    original_metrics = compute_metrics(simulation.schedule.model_dump())
    simulated_metrics = compute_metrics(optimized_sim)
    impact_analysis = {
        "throughput_change": simulated_metrics["throughput_trains_per_hr"] - original_metrics["throughput_trains_per_hr"],
        "delay_change": simulated_metrics["avg_delay_minutes"] - original_metrics["avg_delay_minutes"],
        "punctuality_change": simulated_metrics["punctuality_pct"] - original_metrics["punctuality_pct"],
    }
    return {
        "simulation_id": str(uuid.uuid4()),
        "original_metrics": original_metrics,
        "simulated_metrics": simulated_metrics,
        "impact_analysis": impact_analysis,
        "simulated_schedule": optimized_sim,
        "disruptions_applied": simulation.disruptions,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v1/alerts")
def post_alert(alert: Alert):
    logger.info("Received alert")
    try:
        save_alert(alert.model_dump())
        # DIGITAL TWIN: Add alert to in-memory twin state
        with state_lock:
            digital_twin_state["alerts"].append(alert.model_dump())
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to store alert")
    return {"status": "alert saved"}

@app.get("/api/v1/alerts")
def get_alerts(limit: int = Query(10, ge=1, le=100), level: Optional[str] = Query(None)):
    alerts = get_recent_alerts(limit)
    if level:
        alerts = [alert for alert in alerts if alert.get("level", "").lower() == level.lower()]
    return {
        "alerts": alerts,
        "total": len(alerts),
        "timestamp": datetime.now().isoformat()
    }

@app.websocket("/ws/metrics")
async def websocket_endpoint(websocket: WebSocket, client_id: Optional[str] = None):
    client_id = await manager.connect(websocket, client_id)
    try:
        await websocket.send_text(json.dumps({
            "type": "connection_established",
            "client_id": client_id,
            "timestamp": datetime.now().isoformat()
        }))
        while True:
            data = await websocket.receive_text()
            try:
                message = json.loads(data)
                if message.get("type") == "ping":
                    await websocket.send_text(json.dumps({"type": "pong"}))
            except json.JSONDecodeError:
                logger.warning(f"Invalid JSON received from {client_id}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error for {client_id}: {e}")
        manager.disconnect(websocket)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "version": "1.0.0",
        "active_connections": len(manager.active_connections),
        "services": {
            "optimization": "operational",
            "ai_prediction": "operational",
            "database": "operational",
            "websocket": "operational"
        }
    }
