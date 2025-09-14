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

TIME_FMT = "%H:%M"
MAX_PLATFORMS = int(os.getenv("MAX_PLATFORMS", "10"))
DWELL_MINUTES = int(os.getenv("DWELL_MINUTES", "2"))

def _overlap(a1: str, d1: str, a2: str, d2: str, buffer_minutes: int = DWELL_MINUTES) -> bool:
    start1 = time_to_minutes(a1)
    end1 = time_to_minutes(d1) + buffer_minutes
    start2 = time_to_minutes(a2)
    end2 = time_to_minutes(d2) + buffer_minutes
    return not (end1 <= start2 or end2 <= start1)

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

def predict_delays(trains: List[Train]) -> List[Train]:
    X = np.array([
        [7, 1], [8, 1], [9, 2], [10, 3], [11, 1], [12, 2],
        [13, 3], [14, 1], [15, 2], [16, 1], [17, 3], [18, 2]
    ])
    y = np.array([5, 8, 2, 15, 6, 10, 20, 7, 12, 9, 25, 18])

    try:
        model = LinearRegression()
        model.fit(X, y)
    except Exception as e:
        logger.error(f"Error training ML model: {e}")
        return trains

    for train in trains:
        features = np.array([_train_to_features(train)])
        predicted_delay = model.predict(features)[0]
        train.delay_minutes = max(0, int(np.round(predicted_delay)))
        train.status = "delayed" if train.delay_minutes > 5 else "on_time"
        logger.info(f"AI predicted {train.train_id} will be delayed by {train.delay_minutes} minutes.")
        
    return trains