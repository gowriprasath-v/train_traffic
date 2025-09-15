import os
import logging
from typing import Dict, Any, List, Optional, Tuple
from ortools.sat.python import cp_model
from models import Train, ScheduleRequest
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)
from config import MAX_PLATFORMS, DWELL_MINUTES

def time_to_minutes(timestr: str) -> int:
    """Convert HH:MM time string to minutes from midnight"""
    try:
        if not timestr or not isinstance(timestr, str):
            raise ValueError(f"Invalid time string: {timestr}")
        
        if ':' not in timestr:
            raise ValueError(f"Time must be in HH:MM format: {timestr}")
            
        parts = timestr.split(":")
        if len(parts) != 2:
            raise ValueError(f"Time must be in HH:MM format: {timestr}")
            
        h, m = parts
        hours = int(h)
        minutes = int(m)
        
        if hours < 0 or hours > 23:
            raise ValueError(f"Hours must be 0-23: {hours}")
        if minutes < 0 or minutes > 59:
            raise ValueError(f"Minutes must be 0-59: {minutes}")
            
        return hours * 60 + minutes
        
    except (ValueError, AttributeError) as e:
        logger.error(f"Error converting time '{timestr}': {e}")
        raise ValueError(f"Invalid time format '{timestr}': must be HH:MM")

def minutes_to_time(minutes: int) -> str:
    """Convert minutes from midnight to HH:MM time string"""
    try:
        if not isinstance(minutes, int) or minutes < 0:
            raise ValueError(f"Minutes must be non-negative integer: {minutes}")
        
        # Handle day overflow
        minutes = minutes % (24 * 60)
        
        h, m = divmod(minutes, 60)
        return f"{h:02d}:{m:02d}"
        
    except Exception as e:
        logger.error(f"Error converting minutes {minutes}: {e}")
        return "00:00"

def validate_schedule_data(data: ScheduleRequest) -> List[str]:
    """Validate schedule data and return list of issues"""
    issues = []
    
    if not data.trains:
        issues.append("No trains provided")
        return issues
    
    train_ids = set()
    for i, train in enumerate(data.trains):
        # Check for duplicate train IDs
        if train.train_id in train_ids:
            issues.append(f"Duplicate train ID: {train.train_id}")
        train_ids.add(train.train_id)
        
        # Validate time formats
        try:
            arrival_min = time_to_minutes(train.arrival)
            departure_min = time_to_minutes(train.departure)
            
            if arrival_min >= departure_min:
                issues.append(f"Train {train.train_id}: arrival time must be before departure time")
                
        except ValueError as e:
            issues.append(f"Train {train.train_id}: {e}")
        
        # Validate platform and priority
        if train.platform <= 0 or train.platform > MAX_PLATFORMS:
            issues.append(f"Train {train.train_id}: platform must be 1-{MAX_PLATFORMS}")
        
        if train.priority < 1:
            issues.append(f"Train {train.train_id}: priority must be positive")
    
    return issues

def get_optimized_schedule(data: ScheduleRequest) -> Dict[str, Any]:
    """
    Enhanced train schedule optimization using CP-SAT with comprehensive error handling
    """
    try:
        # Validate input data
        validation_issues = validate_schedule_data(data)
        if validation_issues:
            logger.error(f"Schedule validation failed: {validation_issues}")
            raise ValueError(f"Invalid schedule data: {'; '.join(validation_issues)}")
        
        model = cp_model.CpModel()
        trains: List[Train] = data.trains
        n = len(trains)
        
        if n == 0:
            return {"date": data.date, "trains": []}
        
        logger.info(f"Starting optimization for {n} trains")
        
        # 1. Compute time horizon for scheduling
        try:
            all_times = []
            for t in trains:
                all_times.extend([time_to_minutes(t.arrival), time_to_minutes(t.departure)])
            
            if not all_times:
                raise ValueError("No valid times found in trains")
                
            min_time = min(all_times)
            max_time = max(all_times)
            horizon = max_time + 180  # 3 hours buffer for delays
            
            logger.info(f"Time horizon: {min_time} to {horizon} minutes")
            
        except Exception as e:
            logger.error(f"Error computing time horizon: {e}")
            raise ValueError(f"Invalid time data in schedule: {e}")
        
        # 2. Create decision variables
        platform_vars = [model.NewIntVar(1, MAX_PLATFORMS, f'platform_{i}') for i in range(n)]
        arrival_vars = []
        intervals_by_platform = {p: [] for p in range(1, MAX_PLATFORMS + 1)}
        
        for i, train in enumerate(trains):
            try:
                original_arrival = time_to_minutes(train.arrival)
                original_departure = time_to_minutes(train.departure)
                duration = original_departure - original_arrival
                
                if duration <= 0:
                    logger.warning(f"Train {train.train_id} has non-positive duration, setting to 5 minutes")
                    duration = 5
                
                # Arrival time variable: can be delayed but not advanced
                arrival_var = model.NewIntVar(original_arrival, horizon, f'arrival_{i}')
                arrival_vars.append(arrival_var)
                
                # Create optional interval variables for each possible platform
                is_on_platform_literals = []
                for p in range(1, MAX_PLATFORMS + 1):
                    on_platform = model.NewBoolVar(f'train_{i}_on_platform_{p}')
                    is_on_platform_literals.append(on_platform)
                    
                    # Interval for this train on this platform
                    optional_interval = model.NewOptionalIntervalVar(
                        arrival_var,  # Start time (variable)
                        duration + DWELL_MINUTES,  # Duration (fixed)
                        arrival_var + duration + DWELL_MINUTES,  # End time
                        on_platform,  # Presence literal
                        f'interval_{i}_platform_{p}'
                    )
                    
                    intervals_by_platform[p].append(optional_interval)
                    model.Add(platform_vars[i] == p).OnlyEnforceIf(on_platform)
                
                # Each train must be on exactly one platform
                model.AddExactlyOne(is_on_platform_literals)
                
            except Exception as e:
                logger.error(f"Error creating variables for train {train.train_id}: {e}")
                raise ValueError(f"Failed to create optimization variables for train {train.train_id}")
        
        # 3. Add no-overlap constraints for each platform
        for p in range(1, MAX_PLATFORMS + 1):
            if intervals_by_platform[p]:
                model.AddNoOverlap(intervals_by_platform[p])
        
        # 4. Define objective function
        # Minimize weighted sum of delays and platform changes
        DELAY_COST_WEIGHT = 10
        PLATFORM_CHANGE_COST = 5
        
        total_cost_terms = []
        
        for i, train in enumerate(trains):
            try:
                original_arrival = time_to_minutes(train.arrival)
                priority_weight = max(1, 5 - train.priority)  # Higher priority = higher weight
                
                # Cost for delay
                delay_var = model.NewIntVar(0, horizon, f'delay_{i}')
                model.Add(delay_var == arrival_vars[i] - original_arrival)
                total_cost_terms.append(delay_var * priority_weight * DELAY_COST_WEIGHT)
                
                # Cost for platform change
                is_platform_changed = model.NewBoolVar(f'platform_changed_{i}')
                model.Add(platform_vars[i] != train.platform).OnlyEnforceIf(is_platform_changed)
                model.Add(platform_vars[i] == train.platform).OnlyEnforceIf(is_platform_changed.Not())
                total_cost_terms.append(is_platform_changed * priority_weight * PLATFORM_CHANGE_COST)
                
            except Exception as e:
                logger.error(f"Error creating objective terms for train {train.train_id}: {e}")
                # Continue with other trains
        
        if not total_cost_terms:
            logger.warning("No objective terms created, using dummy objective")
            total_cost_terms = [model.NewIntVar(0, 0, 'dummy_objective')]
        
        model.Minimize(sum(total_cost_terms))
        
        # 5. Solve the model
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = 30.0  # Extended timeout
        solver.parameters.num_search_workers = 4  # Use multiple cores
        
        logger.info("Starting CP-SAT solver...")
        status = solver.Solve(model)
        
        # 6. Process results
        if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
            scheduled_trains = []
            total_delay = 0
            platform_changes = 0
            
            for i, train in enumerate(trains):
                try:
                    train_dict = train.model_dump()
                    
                    original_arrival_min = time_to_minutes(train.arrival)
                    original_departure_min = time_to_minutes(train.departure)
                    duration = original_departure_min - original_arrival_min
                    
                    new_arrival_min = solver.Value(arrival_vars[i])
                    new_departure_min = new_arrival_min + duration
                    new_platform = solver.Value(platform_vars[i])
                    
                    delay_minutes = new_arrival_min - original_arrival_min
                    total_delay += delay_minutes
                    
                    if new_platform != train.platform:
                        platform_changes += 1
                    
                    # Update train data
                    train_dict.update({
                        "platform": new_platform,
                        "arrival": minutes_to_time(new_arrival_min),
                        "departure": minutes_to_time(new_departure_min),
                        "delay_minutes": delay_minutes,
                        "scheduled": train.arrival,  # Keep original scheduled time
                        "status": "delayed" if delay_minutes > 5 else "on_time",
                        "platform_changed": new_platform != train.platform
                    })
                    
                    scheduled_trains.append(train_dict)
                    
                except Exception as e:
                    logger.error(f"Error processing solution for train {train.train_id}: {e}")
                    # Use original train data as fallback
                    scheduled_trains.append(train.model_dump())
            
            optimization_stats = {
                "status": "optimal" if status == cp_model.OPTIMAL else "feasible",
                "total_delay_minutes": total_delay,
                "platform_changes": platform_changes,
                "solve_time_seconds": solver.WallTime(),
                "objective_value": solver.ObjectiveValue() if solver.ObjectiveValue() else 0
            }
            
            logger.info(f"Optimization completed: {optimization_stats}")
            
            return {
                "date": data.date,
                "trains": scheduled_trains,
                "optimization_stats": optimization_stats
            }
        else:
            # Solver failed - return original schedule with warning
            status_names = {
                cp_model.UNKNOWN: "UNKNOWN",
                cp_model.MODEL_INVALID: "MODEL_INVALID",
                cp_model.INFEASIBLE: "INFEASIBLE"
            }
            status_name = status_names.get(status, f"STATUS_{status}")
            
            logger.warning(f"Optimization failed with status: {status_name}. Returning original schedule.")
            
            # Return original schedule as fallback
            fallback_trains = []
            for train in trains:
                train_dict = train.model_dump()
                train_dict["scheduled"] = train.arrival
                train_dict["optimization_note"] = f"Original schedule (optimization failed: {status_name})"
                fallback_trains.append(train_dict)
            
            return {
                "date": data.date,
                "trains": fallback_trains,
                "optimization_stats": {
                    "status": "failed",
                    "reason": status_name,
                    "fallback_used": True
                }
            }
            
    except Exception as e:
        logger.exception(f"Critical error in schedule optimization: {e}")
        
        # Emergency fallback: return original schedule
        try:
            fallback_trains = []
            for train in data.trains:
                train_dict = train.model_dump()
                train_dict["scheduled"] = train.arrival
                train_dict["optimization_note"] = f"Original schedule (optimization error: {str(e)[:100]})"
                fallback_trains.append(train_dict)
            
            return {
                "date": data.date,
                "trains": fallback_trains,
                "optimization_stats": {
                    "status": "error",
                    "error": str(e),
                    "fallback_used": True
                }
            }
        except Exception as fallback_error:
            logger.critical(f"Even fallback failed: {fallback_error}")
            raise ValueError(f"Complete optimization failure: {e}")
