import requests

BACKEND_URL = "http://localhost:8000"

def send_disruption(train_id, delay_minutes, reason):
    url = f"{BACKEND_URL}/api/v1/alerts"
    alert_data = {
        "train_id": train_id,
        "delay_minutes": delay_minutes,
        "reason": reason
    }
    try:
        response = requests.post(url, json=alert_data)
        response.raise_for_status()
        print("Alert sent successfully:", response.json())
    except requests.exceptions.RequestException as e:
        print("Error sending alert:", e)

if __name__ == "__main__":
    send_disruption("12345", 15, "Signal failure")
