import requests
import json
import time
import random
import os
from datetime import datetime, timedelta
import logging
from typing import Dict, List, Optional

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Backend configuration
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
REQUEST_TIMEOUT = 30

class TrafficSimulator:
    """Enhanced traffic simulation with better error handling and scenarios"""
    
    def __init__(self, backend_url: str = BACKEND_URL):
        self.backend_url = backend_url
        self.session = requests.Session()
        self.session.timeout = REQUEST_TIMEOUT
        
        # Simulation scenarios
        self.disruption_scenarios = [
            {"type": "minor_delay", "delay_range": (5, 15), "probability": 0.4},
            {"type": "major_delay", "delay_range": (20, 45), "probability": 0.2},
            {"type": "platform_change", "probability": 0.1},
            {"type": "cancellation", "probability": 0.05},
        ]
    
    def test_connection(self) -> bool:
        """Test if backend is accessible"""
        try:
            response = self.session.get(f"{self.backend_url}/health")
            response.raise_for_status()
            logger.info("Backend connection successful")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Backend connection failed: {e}")
            return False
    
    def get_current_schedule(self) -> Optional[Dict]:
        """Fetch current schedule from backend"""
        try:
            response = self.session.get(f"{self.backend_url}/api/v1/schedule")
            response.raise_for_status()
            data = response.json()
            return data.get("schedule")
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch schedule: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {e}")
            return None
    
    def push_optimized_schedule(self, schedule_data: Dict) -> Optional[Dict]:
        """Send schedule to backend for optimization"""
        try:
            response = self.session.post(
                f"{self.backend_url}/api/v1/optimize",
                json=schedule_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to optimize schedule: {e}")
            if hasattr(e, 'response') and e.response is not None:
                try:
                    error_detail = e.response.json()
                    logger.error(f"Server error details: {error_detail}")
                except:
                    logger.error(f"Server response: {e.response.text}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON response: {e}")
            return None
    
    def simulate_what_if_scenario(self, schedule_data: Dict, disruptions: List[Dict]) -> Optional[Dict]:
        """Test what-if simulation endpoint"""
        try:
            simulation_request = {
                "schedule": schedule_data,
                "disruptions": disruptions
            }
            
            response = self.session.post(
                f"{self.backend_url}/api/v1/simulate",
                json=simulation_request,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to run simulation: {e}")
            return None
    
    def create_alert(self, alert_type: str, message: str, level: str = "warning") -> bool:
        """Create an alert in the system"""
        try:
            alert_data = {
                "alert_type": alert_type,
                "message": message,
                "level": level,
                "timestamp": datetime.now().isoformat()
            }
            
            response = self.session.post(
                f"{self.backend_url}/api/v1/alerts",
                json=alert_data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            logger.info(f"Alert created: {alert_type}")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create alert: {e}")
            return False
    
    def apply_disruption_to_schedule(self, schedule: Dict) -> Dict:
        """Apply realistic disruption to schedule"""
        if not schedule.get("trains"):
            return schedule
        
        # Select random disruption scenario
        scenario = random.choices(
            self.disruption_scenarios,
            weights=[s["probability"] for s in self.disruption_scenarios]
        )[0]
        
        # Select random train
        train_to_disrupt = random.choice(schedule["trains"])
        train_id = train_to_disrupt["train_id"]
        
        if scenario["type"] in ["minor_delay", "major_delay"]:
            delay_range = scenario["delay_range"]
            delay = random.randint(delay_range[0], delay_range[1])
            
            # Update train with delay
            current_delay = train_to_disrupt.get("delay_minutes", 0)
            train_to_disrupt["delay_minutes"] = current_delay + delay
            train_to_disrupt["status"] = "delayed"
            
            # Update arrival and departure times
            try:
                arrival_time = datetime.strptime(train_to_disrupt["arrival"], "%H:%M")
                departure_time = datetime.strptime(train_to_disrupt["departure"], "%H:%M")
                
                new_arrival = arrival_time + timedelta(minutes=delay)
                new_departure = departure_time + timedelta(minutes=delay)
                
                train_to_disrupt["arrival"] = new_arrival.strftime("%H:%M")
                train_to_disrupt["departure"] = new_departure.strftime("%H:%M")
                
                logger.warning(f"Disruption: Train {train_id} delayed by {delay} minutes")
                
                # Create alert
                self.create_alert(
                    "train_delay",
                    f"Train {train_id} delayed by {delay} minutes",
                    "warning" if delay < 20 else "error"
                )
                
            except ValueError as e:
                logger.error(f"Error updating times for train {train_id}: {e}")
        
        elif scenario["type"] == "platform_change":
            original_platform = train_to_disrupt["platform"]
            # Find available platform (simple heuristic)
            used_platforms = {t["platform"] for t in schedule["trains"]}
            available_platforms = set(range(1, 11)) - used_platforms
            
            if available_platforms:
                new_platform = random.choice(list(available_platforms))
                train_to_disrupt["platform"] = new_platform
                logger.warning(f"Disruption: Train {train_id} moved from platform {original_platform} to {new_platform}")
                
                self.create_alert(
                    "platform_change",
                    f"Train {train_id} moved to platform {new_platform}",
                    "info"
                )
        
        elif scenario["type"] == "cancellation":
            train_to_disrupt["status"] = "cancelled"
            logger.warning(f"Disruption: Train {train_id} cancelled")
            
            self.create_alert(
                "train_cancellation",
                f"Train {train_id} has been cancelled",
                "critical"
            )
        
        return schedule
    
    def create_initial_schedule(self) -> Dict:
        """Generate a comprehensive initial schedule for testing"""
        now = datetime.now()
        base_time = now.replace(hour=8, minute=0, second=0, microsecond=0)
        
        # Create diverse train schedule
        train_types = [
            {"prefix": "EXP", "priority": 1, "duration": 5},  # Express trains
            {"prefix": "LOC", "priority": 3, "duration": 3},  # Local trains
            {"prefix": "FRE", "priority": 2, "duration": 10}, # Freight trains
            {"prefix": "SUB", "priority": 2, "duration": 2},  # Suburban trains
        ]
        
        trains = []
        train_counter = 1
        
        for hour_offset in range(0, 12):  # 12 hours of operations
            for i in range(random.randint(2, 4)):  # 2-4 trains per hour
                train_type = random.choice(train_types)
                
                arrival_time = base_time + timedelta(
                    hours=hour_offset,
                    minutes=random.randint(0, 50)
                )
                departure_time = arrival_time + timedelta(minutes=train_type["duration"])
                
                # Avoid late night hours
                if arrival_time.hour >= 22:
                    continue
                
                train = {
                    "train_id": f"{train_type['prefix']}{train_counter:03d}",
                    "arrival": arrival_time.strftime("%H:%M"),
                    "departure": departure_time.strftime("%H:%M"),
                    "priority": train_type["priority"],
                    "platform": random.randint(1, 8),  # 8 platforms available
                    "status": "scheduled",
                    "delay_minutes": 0
                }
                trains.append(train)
                train_counter += 1
        
        return {
            "date": now.strftime("%Y-%m-%d"),
            "trains": trains
        }
    
    def run_continuous_simulation(self, iterations: int = 50, delay_range: tuple = (10, 30)):
        """Run continuous simulation with various scenarios"""
        if not self.test_connection():
            logger.error("Cannot connect to backend. Simulation aborted.")
            return
        
        logger.info(f"Starting continuous simulation with {iterations} iterations")
        
        # Initialize with fresh schedule
        initial_schedule = self.create_initial_schedule()
        result = self.push_optimized_schedule(initial_schedule)
        
        if not result:
            logger.error("Failed to initialize schedule")
            return
        
        logger.info(f"Initial schedule created with {len(initial_schedule['trains'])} trains")
        
        iteration = 0
        while iteration < iterations:
            try:
                iteration += 1
                logger.info(f"--- Simulation Iteration {iteration}/{iterations} ---")
                
                # Get current schedule
                current_schedule = self.get_current_schedule()
                if not current_schedule:
                    logger.error("Failed to fetch current schedule")
                    break
                
                # Test what-if simulation occasionally
                if iteration % 5 == 0:
                    logger.info("Running what-if simulation...")
                    test_disruptions = [
                        {
                            "train_id": random.choice(current_schedule["trains"])["train_id"],
                            "type": "delay",
                            "delay_minutes": random.randint(15, 30)
                        }
                    ]
                    
                    sim_result = self.simulate_what_if_scenario(current_schedule, test_disruptions)
                    if sim_result:
                        logger.info(f"What-if simulation completed. Impact: {sim_result.get('impact_analysis', {})}")
                
                # Apply disruption
                disrupted_schedule = self.apply_disruption_to_schedule(current_schedule)
                
                # Re-optimize
                optimization_result = self.push_optimized_schedule(disrupted_schedule)
                
                if optimization_result:
                    metrics = optimization_result.get("metrics", {})
                    optimization_info = optimization_result.get("optimization_info", {})
                    
                    logger.info(f"Optimization successful:")
                    logger.info(f"  Throughput: {metrics.get('throughput_trains_per_hr', 0)} trains/hr")
                    logger.info(f"  Avg Delay: {metrics.get('avg_delay_minutes', 0)} minutes")
                    logger.info(f"  Punctuality: {metrics.get('punctuality_pct', 0)}%")
                    logger.info(f"  Platform Utilization: {metrics.get('platform_utilization_pct', 0)}%")
                else:
                    logger.error("Optimization failed")
                
                # Random sleep between iterations
                sleep_time = random.randint(delay_range[0], delay_range[1])
                logger.info(f"Waiting {sleep_time} seconds before next iteration...")
                time.sleep(sleep_time)
                
            except KeyboardInterrupt:
                logger.info("Simulation interrupted by user")
                break
            except Exception as e:
                logger.error(f"Error in simulation iteration {iteration}: {e}")
                time.sleep(5)  # Brief pause before continuing
        
        logger.info("Simulation completed")

def main():
    """Main simulation entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Train Traffic Simulation")
    parser.add_argument("--iterations", type=int, default=20, help="Number of simulation iterations")
    parser.add_argument("--delay-min", type=int, default=5, help="Minimum delay between iterations (seconds)")
    parser.add_argument("--delay-max", type=int, default=15, help="Maximum delay between iterations (seconds)")
    parser.add_argument("--backend-url", default=BACKEND_URL, help="Backend URL")
    
    args = parser.parse_args()
    
    simulator = TrafficSimulator(args.backend_url)
    simulator.run_continuous_simulation(
        iterations=args.iterations,
        delay_range=(args.delay_min, args.delay_max)
    )

if __name__ == "__main__":
    main()
