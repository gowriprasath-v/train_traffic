import os
from datetime import datetime, timedelta
from statistics import mean
from typing import Dict, List, Any
from models import ScheduleRequest, Train
from sklearn.linear_model import LinearRegression
import numpy as np
import logging

# IMPORT THE MISSING FUNCTION FROM SCHEDULER
from scheduler import time_to_minutes

logger = logging.getLogger(__name__)

from config import TIME_FMT, MAX_PLATFORMS, DWELL_MINUTES

def compute_metrics(schedule: Dict[str, Any], max_platforms: int | None = None) -> Dict[str, Any]:
    if not schedule or "trains" not in schedule or len(schedule["trains"]) == 0:
        return {
            "throughput_trains_per_hr": 0,
            "avg_delay_minutes": 0,
            "platform_utilization_pct": 0,
            "punctuality_pct": 0
        }

    trains = schedule["trains"]
    times = []
    delays = []
    platforms_used = set()
    punctual_count = 0

    for t in trains:
        try:
            times.append(datetime.strptime(t["arrival"], TIME_FMT))
            times.append(datetime.strptime(t["departure"], TIME_FMT))
        except Exception:
            pass

        platforms_used.add(int(t.get("platform", 0)))

        d = t.get("delay_minutes")
        if isinstance(d, (int, float)):
            delays.append(d)
            if d <= 5:
                punctual_count += 1
        else:
            st = (t.get("status") or "").lower()
            if "on" in st or "time" in st or d == 0:
                punctual_count += 1

    if not times:
        operating_hours = 1.0
    else:
        earliest = min(times)
        latest = max(times)
        span = latest - earliest
        operating_hours = max(span.total_seconds() / 3600.0, 1.0)

    throughput = round(len(trains) / operating_hours, 2)
    avg_delay = round(mean(delays), 2) if delays else 0.0
    max_platforms = (max_platforms or MAX_PLATFORMS)
    platform_util = round((len([p for p in platforms_used if p > 0]) / max_platforms) * 100, 2)
    punctuality_pct = round((punctual_count / len(trains)) * 100, 2)

    return {
        "throughput_trains_per_hr": throughput,
        "avg_delay_minutes": avg_delay,
        "platform_utilization_pct": platform_util,
        "punctuality_pct": punctuality_pct
    }

def _train_to_features(train: Train) -> List[int]:
    arrival_minutes = time_to_minutes(train.arrival)
    hour = arrival_minutes // 60
    return [
        hour, 
        train.priority
    ]

# TODO: Replace this with a proper pre-trained model loading mechanism
def load_delay_prediction_model():
    """
    Placeholder for loading a pre-trained model.
    In a real application, this would load a model from a file
    (e.g., using joblib or pickle).
    """
    # This simple dictionary mimics a basic model's behavior.
    # Key: (hour, priority), Value: predicted_delay
    mock_model = {
        (7, 1): 5, (8, 1): 8, (9, 2): 2, (10, 3): 15, (11, 1): 6, (12, 2): 10,
        (13, 3): 20, (14, 1): 7, (15, 2): 12, (16, 1): 9, (17, 3): 25, (18, 2): 18
    }
    return mock_model

# Load the model once when the module is imported.
delay_model = load_delay_prediction_model()

def predict_delays(trains: List[Train]) -> List[Train]:
    """
    Predicts delays for a list of trains using a pre-loaded model.
    """
    if not delay_model:
        logger.error("Delay prediction model not loaded. Skipping prediction.")
        return trains

    for train in trains:
        try:
            features = tuple(_train_to_features(train))
            # Use a default delay of 0 if features are not in the mock model
            predicted_delay = delay_model.get(features, 0)
            
            train.delay_minutes = max(0, int(np.round(predicted_delay)))
            train.status = "delayed" if train.delay_minutes > 5 else "on_time"
            logger.info(f"AI predicted {train.train_id} will be delayed by {train.delay_minutes} minutes.")
        except Exception as e:
            logger.error(f"Error predicting delay for train {train.train_id}: {e}")
            # Assign a default delay of 0 in case of an error
            train.delay_minutes = 0
            train.status = "on_time"
            
    return trains