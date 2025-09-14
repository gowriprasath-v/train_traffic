import os
import logging
from typing import Dict, Any, List
from ortools.sat.python import cp_model
from models import Train, ScheduleRequest
from datetime import datetime

logger = logging.getLogger(__name__)

MAX_PLATFORMS = int(os.getenv("MAX_PLATFORMS", "10"))
DWELL_MINUTES = int(os.getenv("DWELL_MINUTES", "2"))

def time_to_minutes(timestr: str) -> int:
    h, m = map(int, timestr.split(":"))
    return h * 60 + m

def minutes_to_time(minutes: int) -> str:
    h, m = divmod(minutes, 60)
    return f"{h:02d}:{m:02d}"

def get_optimized_schedule(data: ScheduleRequest) -> Dict[str, Any]:
    model = cp_model.CpModel()
    trains: List[Train] = data.trains
    n = len(trains)

    # Compute horizon for scheduling
    all_times = [time_to_minutes(t.arrival) for t in trains] + [time_to_minutes(t.departure) for t in trains]
    horizon = max(all_times) + 60 if all_times else 1440

    platform_vars = [model.NewIntVar(1, MAX_PLATFORMS, f'platform_{i}') for i in range(n)]
    intervals_by_platform = {p: [] for p in range(1, MAX_PLATFORMS + 1)}

    for i in range(n):
        start = time_to_minutes(trains[i].arrival)
        duration = time_to_minutes(trains[i].departure) - start + DWELL_MINUTES
        end = start + duration

        is_on_platform = []
        for p in range(1, MAX_PLATFORMS + 1):
            on_platform = model.NewBoolVar(f'train_{i}_on_platform_{p}')
            is_on_platform.append(on_platform)

            interval = model.NewOptionalIntervalVar(start, duration, end, on_platform, f'interval_{i}_p_{p}')
            intervals_by_platform[p].append(interval)

            model.Add(platform_vars[i] == p).OnlyEnforceIf(on_platform)
            model.Add(platform_vars[i] != p).OnlyEnforceIf(on_platform.Not())

        model.Add(sum(is_on_platform) == 1)

    for p in range(1, MAX_PLATFORMS + 1):
        model.AddNoOverlap(intervals_by_platform[p])

    # Objective: prioritize trains keeping their requested platform assignment
    objective_terms = []
    for i in range(n):
        preferred = model.NewBoolVar(f'train_{i}_preferred_platform')
        model.Add(platform_vars[i] == trains[i].platform).OnlyEnforceIf(preferred)
        model.Add(platform_vars[i] != trains[i].platform).OnlyEnforceIf(preferred.Not())
        weighted = preferred * (MAX_PLATFORMS + 1 - trains[i].priority)  # higher priority = bigger weight
        objective_terms.append(weighted)

    model.Maximize(sum(objective_terms))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 10.0  # prevent long solving times

    status = solver.Solve(model)

    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        scheduled_trains = []
        for i in range(n):
            tdict = trains[i].model_dump()
            tdict["platform"] = solver.Value(platform_vars[i])
            tdict["status"] = "scheduled"
            scheduled_trains.append(tdict)
        logger.info("Optimized schedule found with CP-SAT solver.")
        return {"date": data.date, "trains": scheduled_trains}
    else:
        logger.warning("No optimal solution found; returning input schedule as fallback.")
        # Fallback: return input schedule unmodified with status "scheduled"
        fallback = []
        for t in trains:
            tdict = t.model_dump()
            tdict["status"] = "scheduled"
            fallback.append(tdict)
        return {"date": data.date, "trains": fallback}
