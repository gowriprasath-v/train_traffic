from pydantic import BaseModel, field_validator, validator
from typing import List, Optional
import re
from datetime import datetime
from config import TIME_FMT, DATE_FMT, TIME_REGEX, DATE_REGEX, MAX_PLATFORMS

class Train(BaseModel):
    train_id: str
    arrival: str
    departure: str
    priority: int
    platform: int

    scheduled: Optional[str] = None
    actual_arrival: Optional[str] = None
    status: Optional[str] = "scheduled"
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
        arr = info.data.get('arrival') or info.data.get('scheduled')
        if arr:
            a = datetime.strptime(arr, TIME_FMT)
            d = datetime.strptime(v, TIME_FMT)
            if a >= d:
                raise ValueError('arrival time must be before departure time')
        return v

    @validator('priority')
    def _priority_non_negative(cls, v):
        if v < 0:
            raise ValueError('priority must be non-negative')
        return v

    @validator('platform')
    def _platform_valid_range(cls, v):
        if v <= 0 or v > MAX_PLATFORMS:
            raise ValueError(f'platform must be between 1 and {MAX_PLATFORMS}')
        return v

class ScheduleRequest(BaseModel):
    date: str
    trains: List[Train]

    @field_validator('date')
    def _check_date_format(cls, v):
        if not re.match(DATE_REGEX, v):
            raise ValueError('date must be YYYY-MM-DD')
        datetime.strptime(v, DATE_FMT)
        return v

class Alert(BaseModel):
    alert_type: str
    message: str
    level: str
    timestamp: str

    @field_validator('timestamp')
    def _check_iso_timestamp(cls, v):
        try:
            datetime.fromisoformat(v)
        except Exception as e:
            raise ValueError("timestamp must be ISO format (e.g. 2025-09-03T17:42:00+05:30)") from e
        return v
