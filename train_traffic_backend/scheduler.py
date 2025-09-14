import os
import logging
from typing import Dict, Any, List
from ortools.sat.python import cp_model
from models import Train, ScheduleRequest
from datetime import datetime

logger = logging.getLogger(__name__)

from config import MAX_PLATFORMS, DWELL_MINUTES

def time_to_minutes(timestr: str) -> int:
    h, m = map(int, timestr.split(":"))
    return h * 60 + m

def minutes_to_time(minutes: int) -> str:
    h, m = divmod(minutes, 60)
    return f"{h:02d}:{m:02d}"

def get_optimized_schedule(data: ScheduleRequest) -> Dict[str, Any]:
    """
    Generates an optimized train schedule using CP-SAT.

    This function now treats arrival times as flexible and aims to minimize
    a weighted cost of delays and platform changes.
    """
    model = cp_model.CpModel()
    trains: List[Train] = data.trains
    n = len(trains)

    # 1. Compute horizon for scheduling
    all_times = [time_to_minutes(t.arrival) for t in trains] + [time_to_minutes(t.departure) for t in trains]
    horizon = max(all_times) + 120 if all_times else 1440  # Increased horizon for potential delays

    # 2. Create decision variables
    platform_vars = [model.NewIntVar(1, MAX_PLATFORMS, f'platform_{i}') for i in range(n)]
    arrival_vars = []
    intervals_by_platform = {p: [] for p in range(1, MAX_PLATFORMS + 1)}

    for i, train in enumerate(trains):
        original_arrival = time_to_minutes(train.arrival)
        duration = time_to_minutes(train.departure) - original_arrival

        # Arrival time is a variable: original time or later
        arrival_var = model.NewIntVar(original_arrival, horizon, f'arrival_{i}')
        arrival_vars.append(arrival_var)

        # Create optional interval variables for each possible platform
        is_on_platform_literals = []
        for p in range(1, MAX_PLATFORMS + 1):
            on_platform = model.NewBoolVar(f'train_{i}_on_platform_{p}')
            is_on_platform_literals.append(on_platform)

            # An optional interval that exists only if the train is on this platform
            optional_interval = model.NewOptionalIntervalVar(
                arrival_var,                                # Start (variable)
                duration + DWELL_MINUTES,                   # Duration (fixed)
                arrival_var + duration + DWELL_MINUTES,     # End (expression)
                on_platform,                                # Presence literal
                f'optional_interval_{i}_p_{p}'
            )
            intervals_by_platform[p].append(optional_interval)
            model.Add(platform_vars[i] == p).OnlyEnforceIf(on_platform)

        # Each train must be on exactly one platform
        model.AddExactlyOne(is_on_platform_literals)

    # 3. Add constraints
    for p in range(1, MAX_PLATFORMS + 1):
        model.AddNoOverlap(intervals_by_platform[p])

    # 4. Define the objective function
    # Minimize a weighted sum of total delay and platform changes.
    DELAY_COST_WEIGHT = 5
    PLATFORM_CHANGE_COST = 10
    total_cost_terms = []

    for i, train in enumerate(trains):
        priority_weight = (MAX_PLATFORMS + 1 - train.priority)

        # A. Cost for delay
        original_arrival = time_to_minutes(train.arrival)
        delay_var = model.NewIntVar(0, horizon, f'delay_{i}')
        model.Add(delay_var == arrival_vars[i] - original_arrival)
        total_cost_terms.append(delay_var * priority_weight * DELAY_COST_WEIGHT)

        # B. Cost for platform change
        is_platform_changed = model.NewBoolVar(f'platform_changed_{i}')
        model.Add(platform_vars[i] != train.platform).OnlyEnforceIf(is_platform_changed)
        model.Add(platform_vars[i] == train.platform).OnlyEnforceIf(is_platform_changed.Not())
        total_cost_terms.append(is_platform_changed * priority_weight * PLATFORM_CHANGE_COST)

    model.Minimize(sum(total_cost_terms))

    # 5. Solve the model
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 20.0  # Increased timeout for a more complex problem
    status = solver.Solve(model)

    # 6. Process the results
    if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
        scheduled_trains = []
        for i, train in enumerate(trains):
            tdict = train.model_dump()
            original_arrival_min = time_to_minutes(train.arrival)
            new_arrival_min = solver.Value(arrival_vars[i])
            original_duration = time_to_minutes(train.departure) - original_arrival_min
            new_departure_min = new_arrival_min + original_duration

            tdict["platform"] = solver.Value(platform_vars[i])
            tdict["arrival"] = minutes_to_time(new_arrival_min)
            tdict["departure"] = minutes_to_time(new_departure_min)
            tdict["delay_minutes"] = new_arrival_min - original_arrival_min
            tdict["status"] = "Delayed" if tdict["delay_minutes"] > 0 else "On time"
            tdict["scheduled"] = train.arrival  # Keep original scheduled time for reference

            scheduled_trains.append(tdict)
        logger.info("Optimized dynamic schedule found with CP-SAT solver.")
        return {"date": data.date, "trains": scheduled_trains}
    else:
        logger.warning("No optimal solution found for dynamic schedule; returning input as fallback.")
        fallback = [t.model_dump() for t in trains]
        return {"date": data.date, "trains": fallback}