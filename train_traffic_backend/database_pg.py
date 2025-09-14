import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from postgresql_models import Base, Schedule, TrainDB
from dotenv import load_dotenv
from contextlib import contextmanager
from datetime import datetime

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in .env")

logger = logging.getLogger(__name__)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def save_schedule_to_db(schedule_data: dict) -> None:
    with get_db() as session:
        try:
            session.query(TrainDB).delete()
            session.query(Schedule).delete()
            session.flush()

            schedule = Schedule(date=schedule_data["date"])
            session.add(schedule)
            session.flush()

            for t in schedule_data.get("trains", []):
                train = TrainDB(
                    train_id=t.get("train_id"),
                    arrival=t.get("arrival"),
                    departure=t.get("departure"),
                    scheduled=t.get("scheduled"),
                    actual_arrival=t.get("actual_arrival"),
                    priority=int(t.get("priority", 0)),
                    platform=int(t.get("platform", 0)),
                    status=t.get("status"),
                    delay_minutes=int(t.get("delay_minutes", 0)),
                    schedule_id=schedule.id
                )
                session.add(train)

            session.commit()
            session.refresh(schedule)
        except SQLAlchemyError:
            session.rollback()
            logger.exception("Failed to save schedule to DB")
            raise



def get_schedule_from_db() -> dict | None:
    with get_db() as session:
        try:
            schedule = session.query(Schedule).first()
            if not schedule:
                return None

            trains = []
            for t in schedule.trains:
                trains.append({
                    "train_id": t.train_id,
                    "arrival": t.arrival,
                    "departure": t.departure,
                    "scheduled": t.scheduled or t.arrival,
                    "actual_arrival": t.actual_arrival or t.arrival,
                    "priority": t.priority,
                    "platform": t.platform,
                    "status": t.status or "On time",
                    "delay_minutes": int(t.delay_minutes or 0)
                })
            
            return {"date": schedule.date, "trains": trains}
        except SQLAlchemyError:
            logger.exception("Failed to read schedule from DB")
            raise
