import requests
from datetime import datetime, timezone

BACKEND_URL = "http://localhost:8000"

def send_disruption():
    url = f"{BACKEND_URL}/api/v1/alerts"
    alert_data = {
        "alert_type": "Delay",
        "message": "Train 12345 delayed 15 minutes due to Signal failure",
        "level": "High",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    try:
        response = requests.post(url, json=alert_data)
        response.raise_for_status()
        print("Alert sent successfully:", response.json())
    except requests.exceptions.RequestException as e:
        print("Error sending alert:", e)

if __name__ == "__main__":
    send_disruption()
