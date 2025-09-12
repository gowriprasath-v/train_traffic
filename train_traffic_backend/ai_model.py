# ai_model.py
"""
ai_model.py
- Single source of scheduling/optimization logic.
- Implements:
    - get_optimized_schedule(data: ScheduleRequest): optimized schedule w/ platform assignment.
    - compute_metrics(schedule_dict): station-level metrics used by the frontend.
Configuration:
    - MAX_PLATFORMS via env (default 10)
    - DWELL_MINUTES via env (default 2)
"""
import os
from datetime import datetime, timedelta
from statistics import mean
from typing import Dict, List, Any
from models import ScheduleRequest

TIME_FMT = "%H:%M"
MAX_PLATFORMS = int(os.getenv("MAX_PLATFORMS", "10"))
DWELL_MINUTES = int(os.getenv("DWELL_MINUTES", "2"))  # buffer after departure in minutes

def _parse_time(t: str) -> datetime:
    return datetime.strptime(t, TIME_FMT)

def _overlap(a1: str, d1: str, a2: str, d2: str, buffer_minutes: int = DWELL_MINUTES) -> bool:
    """
    Return True if [a1,d1 + buffer] overlaps with [a2,d2].
    """
    start1 = _parse_time(a1)
    end1 = _parse_time(d1) + timedelta(minutes=buffer_minutes)
    start2 = _parse_time(a2)
    end2 = _parse_time(d2) + timedelta(minutes=buffer_minutes)
    return not (end1 <= start2 or end2 <= start1)

def get_optimized_schedule(data: ScheduleRequest) -> Dict[str, Any]:
    """
    - Sort trains by (priority, arrival)
    - Assign platforms so trains on same platform don't overlap (within buffer).
    - Try to respect requested platform; if conflict, scan 1..MAX_PLATFORMS to find free one.
    - Return dict: {"date":..., "trains":[{...}, ...]}
    """
    trains_sorted = sorted(data.trains, key=lambda t: (t.priority, t.arrival))
    platform_assignments: Dict[int, List[Dict]] = {}  # platform -> list of train dicts (with arrival/departure)
    scheduled: List[Dict] = []

    for train in trains_sorted:
        # prefer requested platform initially
        assigned = int(train.platform)
        conflict = False
        if assigned in platform_assignments:
            for existing in platform_assignments[assigned]:
                if _overlap(train.arrival, train.departure, existing["arrival"], existing["departure"]):
                    conflict = True
                    break

        if conflict:
            # search for another platform
            found = False
            for p in range(1, MAX_PLATFORMS + 1):
                # check p
                conflict_here = False
                for existing in platform_assignments.get(p, []):
                    if _overlap(train.arrival, train.departure, existing["arrival"], existing["departure"]):
                        conflict_here = True
                        break
                if not conflict_here:
                    assigned = p
                    found = True
                    break
            if not found:
                # no available platform; keep original and mark as conflict
                assigned = int(train.platform)

        # prepare output dict (use model_dump for Pydantic models for Pydantic v2)
        try:
            tdict = train.model_dump()
        except Exception:
            # fallback if train isn't a pydantic model instance
            tdict = {
                "train_id": train.train_id,
                "arrival": train.arrival,
                "departure": train.departure,
                "priority": train.priority,
                "platform": assigned,
            }

        # normalize scheduled/actual fields to be friendly to frontend:
        if "scheduled" not in tdict or tdict.get("scheduled") is None:
            tdict["scheduled"] = tdict.get("arrival")
        if "status" not in tdict or not tdict["status"]:
            tdict["status"] = "scheduled"
        tdict["platform"] = assigned

        scheduled.append(tdict)
        platform_assignments.setdefault(assigned, []).append({
            "arrival": tdict["arrival"],
            "departure": tdict["departure"],
            "train_id": tdict["train_id"]
        })

    return {"date": data.date, "trains": scheduled}


def compute_metrics(schedule: Dict[str, Any], max_platforms: int | None = None) -> Dict[str, Any]:
    """
    Compute metrics required by frontend:
        - throughput: trains per hour (based on earliest arrival to latest departure)
        - avg_delay_minutes
        - platform_utilization: percent of platforms used
        - punctuality_rate: percent trains with delay_minutes <= 5 or status suggests on-time
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

    for t in trains:
        # arrival/departure exist as "HH:MM"
        try:
            times.append(_parse_time(t["arrival"]))
            times.append(_parse_time(t["departure"]))
        except Exception:
            pass

        platforms_used.add(int(t.get("platform", 0)))

        d = t.get("delay_minutes")
        if isinstance(d, (int, float)):
            delays.append(d)
            if d <= 5:
                punctual_count += 1
        else:
            # no delay info -> infer from status
            st = (t.get("status") or "").lower()
            if "on" in st or "time" in st:
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
