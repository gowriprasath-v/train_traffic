import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()
client = MongoClient(os.getenv("MONGO_URI", "mongodb://localhost:27017/"))
db = client["railway_db"]

def save_schedule_to_db(schedule):
    db.schedules.replace_one({}, schedule, upsert=True)

def get_schedule_from_db():
    res = db.schedules.find_one()
    if res:
        res.pop("_id", None)
    return res
