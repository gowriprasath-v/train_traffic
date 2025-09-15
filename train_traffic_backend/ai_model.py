import os
import joblib
from datetime import datetime, timedelta
from statistics import mean
from typing import Dict, List, Any, Optional
from models import ScheduleRequest, Train
import numpy as np
import logging

from scheduler import time_to_minutes
from config import TIME_FMT, MAX_PLATFORMS, DWELL_MINUTES

logger = logging.getLogger(__name__)

def compute_metrics(schedule: Dict[str, Any], max_platforms: Optional[int] = None) -> Dict[str, Any]:
    """
    Compute comprehensive KPIs for the schedule
    """
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
    delayed_count = 0

    for t in trains:
        try:
            arrival_time = datetime.strptime(t["arrival"], TIME_FMT)
            departure_time = datetime.strptime(t["departure"], TIME_FMT)
            times.extend([arrival_time, departure_time])
        except (ValueError, KeyError) as e:
            logger.warning(f"Invalid time format in train {t.get('train_id', 'unknown')}: {e}")
            continue

        # Platform utilization
        platform = t.get("platform", 0)
        if isinstance(platform, (int, float)) and platform > 0:
            platforms_used.add(int(platform))

        # Delay analysis
        delay = t.get("delay_minutes", 0)
        if isinstance(delay, (int, float)):
            delays.append(delay)
            if delay <= 5:  # Consider <= 5 minutes as punctual
                punctual_count += 1
            else:
                delayed_count += 1
        else:
            status = (t.get("status") or "").lower()
            if any(word in status for word in ["on", "time", "punctual"]):
                punctual_count += 1
            elif any(word in status for word in ["delay", "late"]):
                delayed_count += 1

    # Calculate operating hours
    if not times:
        operating_hours = 1.0
    else:
        earliest = min(times)
        latest = max(times)
        span = latest - earliest
        operating_hours = max(span.total_seconds() / 3600.0, 1.0)

    total_trains = len(trains)
    throughput = round(total_trains / operating_hours, 2)
    avg_delay = round(mean(delays), 2) if delays else 0.0
    max_platforms = max_platforms or MAX_PLATFORMS
    platform_util = round((len(platforms_used) / max_platforms) * 100, 2)
    punctuality_pct = round((punctual_count / total_trains) * 100, 2) if total_trains > 0 else 0

    return {
        "throughput_trains_per_hr": throughput,
        "avg_delay_minutes": avg_delay,
        "platform_utilization_pct": platform_util,
        "punctuality_pct": punctuality_pct
    }

def _train_to_features(train: Train) -> List[float]:
    """Convert train data to ML features"""
    try:
        arrival_minutes = time_to_minutes(train.arrival)
        hour = arrival_minutes // 60
        minute = arrival_minutes % 60
        features = [
            hour,                  # Hour of arrival
            minute / 60.0,         # Normalized minute
            train.priority,        # Train priority
            train.platform,        # Platform number
            1.0 if 7 <= hour <= 9 or 17 <= hour <= 19 else 0.0,
            0.0
        ]
        return features
    except Exception as e:
        logger.error(f"Error extracting features for train {train.train_id}: {e}")
        return [0.0] * 6

def load_delay_prediction_model():
    """
    Load a pre-trained delay prediction model.
    In production, this would load from a file (joblib/pickle).
    For demo, we create a more sophisticated mock model.
    """
    try:
        model_path = "delay_model.joblib"
        if os.path.exists(model_path):
            return joblib.load(model_path)
    except Exception as e:
        logger.warning(f"Could not load saved model: {e}")

    mock_predictions = {}
    for hour in range(24):
        for priority in range(1, 4):
            for platform in range(1, MAX_PLATFORMS + 1):
                base_delay = 0
                if 7 <= hour <= 9 or 17 <= hour <= 19:
                    base_delay += 15
                elif 10 <= hour <= 16:
                    base_delay += 5
                base_delay += (priority - 1) * 8
                if platform > MAX_PLATFORMS // 2:
                    base_delay += 3
                variation = (hour * priority * platform) % 10 - 5
                final_delay = max(0, base_delay + variation)
                key = (hour, priority, platform)
                mock_predictions[key] = final_delay
    return mock_predictions

# Load the model once when the module is imported
delay_model = load_delay_prediction_model()

def predict_delays(trains: List[Train]) -> List[Train]:
    """
    Predict delays for a list of trains using the loaded model.
    NOTE: If train.delay_minutes/status already set by user, do NOT overwrite.
    """
    if not delay_model:
        logger.error("Delay prediction model not loaded. Skipping prediction.")
        return trains

    for train in trains:
        # Don't overwrite manual values
        delay_set = getattr(train, 'delay_minutes', None)
        status_set = getattr(train, 'status', '').lower() in {"on_time", "delayed", "minor_delay", "cancelled"}
        if delay_set not in (None, 0) or status_set:
            continue
        try:
            features = _train_to_features(train)
            hour = int(features[0])
            priority = train.priority
            platform = train.platform
            key = (hour, priority, platform)
            predicted_delay = delay_model.get(key, 0)
            # Add contextual adjustments
            if isinstance(delay_model, dict):
                if hour in [7, 8, 17, 18]:
                    predicted_delay += np.random.normal(5, 2)
                predicted_delay = max(0, int(np.round(predicted_delay)))
            train.delay_minutes = predicted_delay
            if predicted_delay <= 5:
                train.status = "on_time"
            elif predicted_delay <= 15:
                train.status = "minor_delay"
            else:
                train.status = "delayed"
        except Exception as e:
            logger.error(f"Error predicting delay for train {train.train_id}: {e}")
            train.delay_minutes = 0
            train.status = "on_time"
    return trains

def generate_delay_explanation(train: Train, predicted_delay: int) -> str:
    """Generate human-readable explanation for delay prediction"""
    explanations = []
    arrival_hour = time_to_minutes(train.arrival) // 60
    if arrival_hour in [7, 8, 9, 17, 18, 19]:
        explanations.append("peak traffic hours")
    if train.priority > 2:
        explanations.append("lower priority train")
    if train.platform > MAX_PLATFORMS // 2:
        explanations.append("platform location")
    if predicted_delay == 0:
        return "Expected on-time arrival"
    elif predicted_delay <= 5:
        return f"Minor delay expected ({predicted_delay}min) - within acceptable range"
    else:
        base_msg = f"Delay predicted: {predicted_delay} minutes"
        if explanations:
            base_msg += f" due to {', '.join(explanations)}"
        return base_msg
