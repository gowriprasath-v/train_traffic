# config.py
import os

# --- Time & Date Formats ---
TIME_FMT = "%H:%M"
DATE_FMT = "%Y-%m-%d"
TIME_REGEX = r"^(?:[01]\d|2[0-3]):[0-5]\d$"
DATE_REGEX = r"^\d{4}-\d{2}-\d{2}$"

# --- Railway Operations ---
# Maximum number of platforms available in the station
MAX_PLATFORMS = int(os.getenv("MAX_PLATFORMS", "10"))

# Default time in minutes a train must wait at a platform
DWELL_MINUTES = int(os.getenv("DWELL_MINUTES", "2"))
