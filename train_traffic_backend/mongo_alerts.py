import os
import logging
from pymongo import MongoClient, errors
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
if not MONGO_URI:
    raise RuntimeError("MONGO_URI is not set in .env")

logger = logging.getLogger(__name__)

try:
    client = MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)
    client.server_info()
except Exception as e:
    logger.exception("Could not connect to MongoDB - check MONGO_URI and network")
    raise

db = client["team3_alerts"]
alerts_collection = db.get_collection("alerts")

def save_alert(alert_data: dict) -> None:
    if "timestamp" not in alert_data or not alert_data["timestamp"]:
        alert_data["timestamp"] = datetime.utcnow().isoformat()
    try:
        alerts_collection.insert_one(alert_data)
    except errors.PyMongoError:
        logger.exception("Failed to insert alert into MongoDB")
        raise

def get_recent_alerts(limit: int = 10) -> list[dict]:
    try:
        cursor = alerts_collection.find().sort("timestamp", -1).limit(limit)
        results = []
        for a in cursor:
            a.pop("_id", None)
            results.append(a)
        return results
    except errors.PyMongoError:
        logger.exception("Failed to read alerts from MongoDB")
        raise
