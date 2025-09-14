import requests
import json
import time
import random
from datetime import datetime, timedelta
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Assumes the FastAPI backend is running on localhost:8000
BACKEND_URL = "http://localhost:8000"

def get_current_schedule():
    """Fetches the current schedule from the backend."""
    try:
        response = requests.get(f"{BACKEND_URL}/api/v1/schedule")
        response.raise_for_status()
        return response.json()["schedule"]
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch schedule: {e}")
        return None

def push_optimized_schedule(schedule_data):
    """Sends a schedule to the backend for optimization."""
    try:
        response = requests.post(f"{BACKEND_URL}/api/v1/optimize", json=schedule_data)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to push optimized schedule: {e}")
        return None

def simulate_disruption(schedule):
    """Simulates a random disruption in the schedule."""
    if not schedule["trains"]:
        return schedule
    
    # Pick a random train to delay
    train_to_delay = random.choice(schedule["trains"])
    
    # Add a random delay between 5 and 30 minutes
    delay = random.randint(5, 30)
    train_to_delay["delay_minutes"] = delay
    train_to_delay["status"] = "delayed"
    
    # Update the actual arrival and departure times based on the delay
    arrival_time = datetime.strptime(train_to_delay["arrival"], "%H:%M")
    departure_time = datetime.strptime(train_to_delay["departure"], "%H:%M")
    
    new_arrival = arrival_time + timedelta(minutes=delay)
    new_departure = departure_time + timedelta(minutes=delay)
    
    train_to_delay["arrival"] = new_arrival.strftime("%H:%M")
    train_to_delay["departure"] = new_departure.strftime("%H:%M")

    logger.warning(f"Simulating disruption: Train {train_to_delay['train_id']} delayed by {delay} minutes.")
    
    return schedule

def create_initial_schedule():
    """Generates a dummy initial schedule for the demo."""
    now = datetime.now()
    initial_trains = [
        {"train_id": "EXP101", "arrival": (now + timedelta(minutes=10)).strftime("%H:%M"), "departure": (now + timedelta(minutes=15)).strftime("%H:%M"), "priority": 1, "platform": 1},
        {"train_id": "LOC202", "arrival": (now + timedelta(minutes=13)).strftime("%H:%M"), "departure": (now + timedelta(minutes=18)).strftime("%H:%M"), "priority": 3, "platform": 1},
        {"train_id": "FRE303", "arrival": (now + timedelta(minutes=20)).strftime("%H:%M"), "departure": (now + timedelta(minutes=25)).strftime("%H:%M"), "priority": 2, "platform": 2},
        {"train_id": "EXP102", "arrival": (now + timedelta(minutes=22)).strftime("%H:%M"), "departure": (now + timedelta(minutes=27)).strftime("%H:%M"), "priority": 1, "platform": 2},
    ]
    return {"date": now.strftime("%Y-%m-%d"), "trains": initial_trains}

if __name__ == "__main__":
    logger.info("Starting simulation script...")
    
    # Push initial schedule to get started
    initial_schedule = create_initial_schedule()
    push_optimized_schedule(initial_schedule)
    logger.info("Initial schedule pushed and optimized.")

    while True:
        # Fetch the current state from the backend
        current_schedule = get_current_schedule()
        if current_schedule:
            # Introduce a random delay to simulate a disruption
            disrupted_schedule = simulate_disruption(current_schedule)
            
            # Send the new, disrupted schedule to the backend for re-optimization
            push_optimized_schedule(disrupted_schedule)
            
        # Wait for a random interval before the next disruption
        sleep_time = random.randint(5, 15)
        logger.info(f"Waiting for {sleep_time} seconds before next disruption.")
        time.sleep(sleep_time)
