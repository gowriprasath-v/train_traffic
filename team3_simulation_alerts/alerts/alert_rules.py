import sys
import os

# Add api_test folder to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'api_test')))

import test_schedule_api as schedule_api

def check_for_alerts(trains):
    alerts = []
    for train in trains:
        train_id = train.get('train_id', 'Unknown')
        delay_minutes = train.get('delay_minutes', 0)
        if delay_minutes > 5:
            alerts.append(f"Train {train_id} delayed by {delay_minutes} minutes")
        if train.get('status') == 'Cancelled':
            alerts.append(f"Train {train_id} is cancelled")
    return alerts

if __name__ == "__main__":
    schedule = schedule_api.fetch_schedule()
    if schedule and "trains" in schedule:
        alert_list = check_for_alerts(schedule["trains"])
        for alert in alert_list:
            print(alert)
    else:
        print("No train data found in schedule.")
