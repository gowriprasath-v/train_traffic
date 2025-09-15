# config.py - Enhanced configuration management

import os
from typing import Optional

# --- Time & Date Formats ---
TIME_FMT = "%H:%M"
DATE_FMT = "%Y-%m-%d"
DATETIME_FMT = "%Y-%m-%d %H:%M:%S"
ISO_DATETIME_FMT = "%Y-%m-%dT%H:%M:%S"

# --- Validation Patterns ---
TIME_REGEX = r"^(?:[01]\d|2[0-3]):[0-5]\d$"
DATE_REGEX = r"^\d{4}-\d{2}-\d{2}$"
TRAIN_ID_REGEX = r"^[A-Z]{2,4}\d{2,4}$"  # e.g., EXP101, LOC1234

# --- Railway Operations ---
# Maximum number of platforms available in the station
MAX_PLATFORMS = int(os.getenv("MAX_PLATFORMS", "10"))

# Default time in minutes a train must wait at a platform
DWELL_MINUTES = int(os.getenv("DWELL_MINUTES", "2"))

# Minimum separation between trains on same platform (minutes)
MIN_SEPARATION_MINUTES = int(os.getenv("MIN_SEPARATION_MINUTES", "5"))

# Maximum delay allowed before escalation (minutes)
MAX_ACCEPTABLE_DELAY = int(os.getenv("MAX_ACCEPTABLE_DELAY", "15"))

# --- AI/ML Configuration ---
# Model training parameters
AI_MODEL_VERSION = os.getenv("AI_MODEL_VERSION", "1.0")
AI_CONFIDENCE_THRESHOLD = float(os.getenv("AI_CONFIDENCE_THRESHOLD", "0.8"))

# Feature weights for delay prediction
RUSH_HOUR_WEIGHT = float(os.getenv("RUSH_HOUR_WEIGHT", "2.0"))
PRIORITY_WEIGHT = float(os.getenv("PRIORITY_WEIGHT", "1.5"))
PLATFORM_WEIGHT = float(os.getenv("PLATFORM_WEIGHT", "1.2"))

# --- Optimization Parameters ---
# CP-SAT solver configuration
SOLVER_TIMEOUT_SECONDS = int(os.getenv("SOLVER_TIMEOUT_SECONDS", "30"))
SOLVER_THREADS = int(os.getenv("SOLVER_THREADS", "4"))

# Optimization objective weights
DELAY_COST_WEIGHT = int(os.getenv("DELAY_COST_WEIGHT", "10"))
PLATFORM_CHANGE_COST = int(os.getenv("PLATFORM_CHANGE_COST", "5"))
THROUGHPUT_WEIGHT = float(os.getenv("THROUGHPUT_WEIGHT", "1.0"))

# --- Train Priority Levels ---
PRIORITY_HIGH = 1      # Express trains
PRIORITY_MEDIUM = 2    # Regular passenger trains
PRIORITY_LOW = 3       # Freight trains

# Priority descriptions for UI
PRIORITY_DESCRIPTIONS = {
    PRIORITY_HIGH: "High Priority (Express)",
    PRIORITY_MEDIUM: "Medium Priority (Regular)",
    PRIORITY_LOW: "Low Priority (Freight)"
}

# --- Alert Levels ---
ALERT_LEVELS = ["info", "warning", "error", "critical"]
ALERT_TYPES = [
    "train_delay",
    "platform_change", 
    "train_cancellation",
    "system_optimization",
    "conflict_detected",
    "capacity_warning"
]

# --- Rush Hour Definitions ---
MORNING_RUSH_START = int(os.getenv("MORNING_RUSH_START", "7"))  # 7 AM
MORNING_RUSH_END = int(os.getenv("MORNING_RUSH_END", "9"))      # 9 AM
EVENING_RUSH_START = int(os.getenv("EVENING_RUSH_START", "17")) # 5 PM
EVENING_RUSH_END = int(os.getenv("EVENING_RUSH_END", "19"))     # 7 PM

# --- Validation Functions ---
def validate_time_format(time_str: str) -> bool:
    """Validate time string format"""
    import re
    return bool(re.match(TIME_REGEX, time_str))

def validate_date_format(date_str: str) -> bool:
    """Validate date string format"""
    import re
    return bool(re.match(DATE_REGEX, date_str))

def is_rush_hour(hour: int) -> bool:
    """Check if given hour is during rush hour"""
    return ((MORNING_RUSH_START <= hour < MORNING_RUSH_END) or 
            (EVENING_RUSH_START <= hour < EVENING_RUSH_END))

def get_priority_description(priority: int) -> str:
    """Get human-readable priority description"""
    return PRIORITY_DESCRIPTIONS.get(priority, f"Priority {priority}")

# --- Export commonly used values ---
__all__ = [
    'TIME_FMT', 'DATE_FMT', 'TIME_REGEX', 'DATE_REGEX',
    'MAX_PLATFORMS', 'DWELL_MINUTES', 'MIN_SEPARATION_MINUTES',
    'SOLVER_TIMEOUT_SECONDS', 'DELAY_COST_WEIGHT', 'PLATFORM_CHANGE_COST',
    'PRIORITY_HIGH', 'PRIORITY_MEDIUM', 'PRIORITY_LOW',
    'validate_time_format', 'validate_date_format', 'is_rush_hour'
]
