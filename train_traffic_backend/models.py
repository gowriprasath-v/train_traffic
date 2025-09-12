# models.py
from pydantic import BaseModel, field_validator
from typing import List, Optional
import re
from datetime import datetime

TIME_FMT = "%H:%M"
DATE_FMT = "%Y-%m-%d"
TIME_REGEX = r"^(?:[01]\d|2[0-3]):[0-5]\d$"
DATE_REGEX = r"^\d{4}-\d{2}-\d{2}$"

class Train(BaseModel):
    """
    Train model used for requests/responses.
    - arrival/departure: expected "HH:MM" 24-hour strings (by default these are scheduled times).
    - Optional fields allow the frontend to display 'scheduled' vs 'actual' if provided later.
    """
    train_id: str
    arrival: str        # scheduled arrival "HH:MM" (keeps backward compatibility)
    departure: str      # scheduled departure "HH:MM"
    priority: int       # lower = higher priority
    platform: int

    # Optional / additional fields (frontend-friendly; not mandatory)
    scheduled: Optional[str] = None        # if frontend wants explicit "Scheduled" column
    actual_arrival: Optional[str] = None   # actual arrival time (if known)
    status: Optional[str] = "scheduled"    # e.g. "on_time", "delayed", "cancelled"
    delay_minutes: Optional[int] = 0

    @field_validator('arrival', 'departure', 'scheduled', 'actual_arrival', mode='before')
    def _check_time_format(cls, v, info):
        if v is None:
            return v
        if not re.match(TIME_REGEX, v):
            raise ValueError("time must be in HH:MM 24-hour format")
        return v

    @field_validator('departure')
    def _arrival_before_departure(cls, v, info):
        # `info.data` contains all fields parsed so far; use arrival or scheduled (fallback)
        arr = info.data.get('arrival') or info.data.get('scheduled')
        if arr:
            a = datetime.strptime(arr, TIME_FMT)
            d = datetime.strptime(v, TIME_FMT)
            if a >= d:
                raise ValueError('arrival time must be before departure time')
        return v

    @field_validator('priority')
    def _priority_non_negative(cls, v):
        if v < 0:
            raise ValueError('priority must be non-negative')
        return v

    @field_validator('platform')
    def _platform_positive(cls, v):
        if v <= 0:
            raise ValueError('platform must be a positive integer')
        return v

class ScheduleRequest(BaseModel):
    date: str                # "YYYY-MM-DD"
    trains: List[Train]

    @field_validator('date')
    def _check_date_format(cls, v):
        if not re.match(DATE_REGEX, v):
            raise ValueError('date must be YYYY-MM-DD')
        # also ensure a valid date (will raise if invalid)
        datetime.strptime(v, DATE_FMT)
        return v

class Alert(BaseModel):
    alert_type: str
    message: str
    level: str           # "info", "warning", "critical", etc.
    timestamp: str       # ISO format recommended

    @field_validator('timestamp')
    def _check_iso_timestamp(cls, v):
        # allow naive or offset-aware ISO; this will raise on bad formats
        try:
            datetime.fromisoformat(v)
        except Exception as e:
            raise ValueError("timestamp must be ISO format (e.g. 2025-09-03T17:42:00+05:30)") from e
        return v
