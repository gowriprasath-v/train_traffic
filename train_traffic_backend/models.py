from pydantic import BaseModel, field_validator
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

    @field_validator('arrival', 'departure', 'scheduled', 'actual_arrival')
    @classmethod
    def _check_time_format(cls, v):
        if v is None:
            return v
        if not re.match(TIME_REGEX, v):
            raise ValueError("time must be in HH:MM 24-hour format")
        return v

    @field_validator('departure')
    @classmethod
    def _arrival_before_departure(cls, v, info):
        if info.data is None:
            return v
        arr = info.data.get('arrival') or info.data.get('scheduled')
        if arr and v:
            try:
                a = datetime.strptime(arr, TIME_FMT)
                d = datetime.strptime(v, TIME_FMT)
                if a >= d:
                    raise ValueError('arrival time must be before departure time')
            except ValueError as e:
                if "time data" in str(e):
                    raise ValueError("Invalid time format")
                raise
        return v

    @field_validator('priority')
    @classmethod
    def _priority_non_negative(cls, v):
        if v < 0:
            raise ValueError('priority must be non-negative')
        return v

    @field_validator('platform')
    @classmethod
    def _platform_valid_range(cls, v):
        if v <= 0 or v > MAX_PLATFORMS:
            raise ValueError(f'platform must be between 1 and {MAX_PLATFORMS}')
        return v

    @field_validator('train_id')
    @classmethod
    def _train_id_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('train_id cannot be empty')
        return v.strip()

class ScheduleRequest(BaseModel):
    date: str
    trains: List[Train]

    @field_validator('date')
    @classmethod
    def _check_date_format(cls, v):
        if not re.match(DATE_REGEX, v):
            raise ValueError('date must be YYYY-MM-DD')
        try:
            datetime.strptime(v, DATE_FMT)
        except ValueError:
            raise ValueError('Invalid date format')
        return v

    @field_validator('trains')
    @classmethod
    def _check_trains_not_empty(cls, v):
        if not v:
            raise ValueError('At least one train must be provided')
        # Check for duplicate train IDs
        train_ids = [train.train_id for train in v]
        if len(train_ids) != len(set(train_ids)):
            raise ValueError('Duplicate train IDs are not allowed')
        return v

class Alert(BaseModel):
    alert_type: str
    message: str
    level: str
    timestamp: str

    @field_validator('timestamp')
    @classmethod
    def _check_iso_timestamp(cls, v):
        try:
            datetime.fromisoformat(v)
        except Exception as e:
            raise ValueError("timestamp must be ISO format (e.g. 2025-09-03T17:42:00+05:30)") from e
        return v

    @field_validator('alert_type', 'message', 'level')
    @classmethod
    def _check_not_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('Field cannot be empty')
        return v.strip()

class SimulationRequest(BaseModel):
    """New model for what-if simulation requests"""
    schedule: ScheduleRequest
    disruptions: List[dict] = []  # List of disruption scenarios
    
    @field_validator('disruptions')
    @classmethod
    def _validate_disruptions(cls, v):
        for disruption in v:
            if 'train_id' not in disruption:
                raise ValueError('Each disruption must have a train_id')
            if 'type' not in disruption:
                raise ValueError('Each disruption must have a type')
        return v
