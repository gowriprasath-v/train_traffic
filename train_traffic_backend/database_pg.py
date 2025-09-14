import os
import logging
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import sessionmaker, Session, declarative_base, relationship
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.sql import func
from dotenv import load_dotenv
from datetime import datetime
from typing import Dict

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in .env")

logger = logging.getLogger(__name__)

Base = declarative_base()

def sort_trains_by_arrival(trains):
    def arrival_key(t):
        try:
            return datetime.strptime(t["arrival"], "%H:%M")
        except Exception:
            return datetime.strptime("00:00", "%H:%M")
    return sorted(trains, key=arrival_key)

class Schedule(Base):
    __tablename__ = "schedules"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, unique=True, nullable=False)
    version = Column(Integer, default=1)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    trains = relationship("TrainDB", back_populates="schedule", cascade="all, delete-orphan")

class TrainDB(Base):
    __tablename__ = "trains"
    id = Column(Integer, primary_key=True, index=True)
    train_id = Column(String, nullable=False)
    arrival = Column(String, nullable=False)
    departure = Column(String, nullable=False)
    scheduled = Column(String, nullable=True)
    actual_arrival = Column(String, nullable=True)
    priority = Column(Integer, nullable=False)
    platform = Column(Integer, nullable=False)
    status = Column(String, nullable=True)
    delay_minutes = Column(Integer, nullable=False, server_default="0")

    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=False)
    schedule = relationship("Schedule", back_populates="trains")

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def save_schedule_to_db(schedule_data: Dict, db: Session) -> None:
    try:
        schedule_date = schedule_data["date"]
        existing_schedule = db.query(Schedule).filter_by(date=schedule_date).first()

        if existing_schedule:
            existing_schedule.version += 1
            db.add(existing_schedule)
            db.flush()

            existing_trains = {t.train_id: t for t in existing_schedule.trains}
            incoming_trains = {t["train_id"]: t for t in schedule_data.get("trains", [])}

            for train_id, db_train in existing_trains.items():
                if train_id in incoming_trains:
                    incoming = incoming_trains[train_id]
                    db_train.arrival = incoming.get("arrival")
                    db_train.departure = incoming.get("departure")
                    db_train.scheduled = incoming.get("scheduled")
                    db_train.actual_arrival = incoming.get("actual_arrival")
                    db_train.priority = int(incoming.get("priority", 0))
                    db_train.platform = int(incoming.get("platform", 0))
                    db_train.status = incoming.get("status")
                    db_train.delay_minutes = int(incoming.get("delay_minutes", 0))
                else:
                    db.delete(db_train)

            for train_id, incoming in incoming_trains.items():
                if train_id not in existing_trains:
                    train = TrainDB(
                        train_id=train_id,
                        arrival=incoming.get("arrival"),
                        departure=incoming.get("departure"),
                        scheduled=incoming.get("scheduled"),
                        actual_arrival=incoming.get("actual_arrival"),
                        priority=int(incoming.get("priority", 0)),
                        platform=int(incoming.get("platform", 0)),
                        status=incoming.get("status"),
                        delay_minutes=int(incoming.get("delay_minutes", 0)),
                        schedule_id=existing_schedule.id
                    )
                    db.add(train)

        else:
            new_schedule = Schedule(date=schedule_date, version=1)
            db.add(new_schedule)
            db.flush()

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
                    schedule_id=new_schedule.id
                )
                db.add(train)

        db.commit()
    except SQLAlchemyError:
        db.rollback()
        logger.exception("Failed to save schedule to DB")
        raise

def get_schedule_from_db(db: Session) -> dict | None:
    try:
        schedule = db.query(Schedule).order_by(Schedule.date.desc()).first()
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

        trains = sort_trains_by_arrival(trains)

        return {"date": schedule.date, "version": schedule.version, "trains": trains}
    except SQLAlchemyError:
        logger.exception("Failed to read schedule from DB")
        raise
