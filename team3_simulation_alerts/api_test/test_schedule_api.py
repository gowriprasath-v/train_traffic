import requests

BACKEND_URL = "http://localhost:8000"

def fetch_schedule():
    url = f"{BACKEND_URL}/api/v1/schedule"
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        print("Schedule Data:", data.get("schedule"))
        return data.get("schedule")
    except requests.exceptions.RequestException as e:
        print("Error fetching schedule:", e)
        return None

if __name__ == "__main__":
    fetch_schedule()
