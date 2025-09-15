import os
import logging
from contextlib import contextmanager
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, Text, Index
from sqlalchemy.orm import sessionmaker, Session, declarative_base, relationship
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.sql import func
from sqlalchemy.pool import QueuePool
from dotenv import load_dotenv
from datetime import datetime, timedelta
from typing import Dict, Optional, List
import json

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set in .env")

logger = logging.getLogger(__name__)

Base = declarative_base()

def sort_trains_by_arrival(trains):
    """Enhanced train sorting with error handling"""
    def arrival_key(t):
        try:
            return datetime.strptime(t["arrival"], "%H:%M")
        except (ValueError, KeyError, TypeError):
            logger.warning(f"Invalid arrival time for train {t.get('train_id', 'unknown')}")
            return datetime.strptime("00:00", "%H:%M")
    
    if not trains:
        return []
    
    return sorted(trains, key=arrival_key)

class Schedule(Base):
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    date = Column(String(10), nullable=False, index=True)  # YYYY-MM-DD format
    version = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())
    notes = Column(Text, nullable=True)  # For additional metadata
    
    # Relationships
    trains = relationship("TrainDB", back_populates="schedule", cascade="all, delete-orphan")
    
    # Indexes for better performance
    __table_args__ = (
        Index('idx_schedule_date_version', 'date', 'version'),
    )

class TrainDB(Base):
    __tablename__ = "trains"
    
    id = Column(Integer, primary_key=True, index=True)
    
    # Core fields
    train_id = Column(String(50), nullable=False, index=True)
    arrival = Column(String(5), nullable=False)  # HH:MM format
    departure = Column(String(5), nullable=False)  # HH:MM format
    
    # Additional tracking fields
    scheduled = Column(String(5), nullable=True)  # Original scheduled time
    actual_arrival = Column(String(5), nullable=True)  # Actual arrival time
    
    # Operational fields
    priority = Column(Integer, nullable=False, default=3)
    platform = Column(Integer, nullable=False)
    status = Column(String(20), nullable=True, default="scheduled")
    delay_minutes = Column(Integer, nullable=False, server_default="0")
    
    # AI/Explanation field
    explanation = Column(Text, nullable=True)  # AI explanation for decisions
    
    # Foreign key
    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=False)
    
    # Relationship
    schedule = relationship("Schedule", back_populates="trains")
    
    # Indexes for better performance
    __table_args__ = (
        Index('idx_train_id_schedule', 'train_id', 'schedule_id'),
        Index('idx_platform_arrival', 'platform', 'arrival'),
    )

# Enhanced engine configuration with connection pooling
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=3600,
    echo=False  # Set to True for SQL debugging
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Error creating database tables: {e}")
    raise

def get_db():
    """Dependency for FastAPI"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def save_schedule_to_db(schedule_data: Dict, db: Session) -> None:
    """
    Enhanced schedule saving with better error handling and validation
    """
    if not schedule_data or not isinstance(schedule_data, dict):
        raise ValueError("Invalid schedule data provided")
    
    if "date" not in schedule_data:
        raise ValueError("Schedule date is required")
    
    if "trains" not in schedule_data or not schedule_data["trains"]:
        raise ValueError("At least one train is required in schedule")
    
    try:
        schedule_date = schedule_data["date"]
        trains_data = schedule_data.get("trains", [])
        
        # Validate date format
        try:
            datetime.strptime(schedule_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError(f"Invalid date format: {schedule_date}")
        
        # Check for existing schedule
        existing_schedule = db.query(Schedule).filter_by(date=schedule_date).first()
        
        if existing_schedule:
            # Update existing schedule
            existing_schedule.version += 1
            existing_schedule.updated_at = func.now()
            db.flush()
            
            # Get existing trains
            existing_trains = {t.train_id: t for t in existing_schedule.trains}
            incoming_trains = {t["train_id"]: t for t in trains_data}
            
            # Update or delete existing trains
            for train_id, db_train in existing_trains.items():
                if train_id in incoming_trains:
                    # Update existing train
                    incoming = incoming_trains[train_id]
                    db_train.arrival = incoming.get("arrival")
                    db_train.departure = incoming.get("departure")
                    db_train.scheduled = incoming.get("scheduled")
                    db_train.actual_arrival = incoming.get("actual_arrival")
                    db_train.priority = int(incoming.get("priority", 3))
                    db_train.platform = int(incoming.get("platform", 1))
                    db_train.status = incoming.get("status", "scheduled")
                    db_train.delay_minutes = int(incoming.get("delay_minutes", 0))
                    db_train.explanation = incoming.get("explanation")
                else:
                    # Remove train not in new schedule
                    db.delete(db_train)
            
            # Add new trains
            for train_id, incoming in incoming_trains.items():
                if train_id not in existing_trains:
                    train = TrainDB(
                        train_id=train_id,
                        arrival=incoming.get("arrival"),
                        departure=incoming.get("departure"),
                        scheduled=incoming.get("scheduled"),
                        actual_arrival=incoming.get("actual_arrival"),
                        priority=int(incoming.get("priority", 3)),
                        platform=int(incoming.get("platform", 1)),
                        status=incoming.get("status", "scheduled"),
                        delay_minutes=int(incoming.get("delay_minutes", 0)),
                        explanation=incoming.get("explanation"),
                        schedule_id=existing_schedule.id
                    )
                    db.add(train)
        else:
            # Create new schedule
            new_schedule = Schedule(
                date=schedule_date, 
                version=1,
                notes=schedule_data.get("notes")
            )
            db.add(new_schedule)
            db.flush()
            
            # Add all trains
            for train_data in trains_data:
                train = TrainDB(
                    train_id=train_data.get("train_id"),
                    arrival=train_data.get("arrival"),
                    departure=train_data.get("departure"),
                    scheduled=train_data.get("scheduled"),
                    actual_arrival=train_data.get("actual_arrival"),
                    priority=int(train_data.get("priority", 3)),
                    platform=int(train_data.get("platform", 1)),
                    status=train_data.get("status", "scheduled"),
                    delay_minutes=int(train_data.get("delay_minutes", 0)),
                    explanation=train_data.get("explanation"),
                    schedule_id=new_schedule.id
                )
                db.add(train)
        
        db.commit()
        logger.info(f"Schedule saved successfully for date: {schedule_date}")
        
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error: {e}")
        raise ValueError("Database constraint violation")
    except SQLAlchemyError as e:
        db.rollback()
        logger.exception(f"Database error while saving schedule: {e}")
        raise
    except Exception as e:
        db.rollback()
        logger.exception(f"Unexpected error while saving schedule: {e}")
        raise

def get_schedule_from_db(db: Session, date: Optional[str] = None) -> Optional[Dict]:
    """
    Enhanced schedule retrieval with optional date filtering
    """
    try:
        query = db.query(Schedule)
        
        if date:
            # Validate date format
            try:
                datetime.strptime(date, "%Y-%m-%d")
                schedule = query.filter_by(date=date).order_by(Schedule.version.desc()).first()
            except ValueError:
                raise ValueError(f"Invalid date format: {date}")
        else:
            # Get most recent schedule
            schedule = query.order_by(Schedule.date.desc(), Schedule.version.desc()).first()
        
        if not schedule:
            return None

        trains = []
        for t in schedule.trains:
            train_dict = {
                "train_id": t.train_id,
                "arrival": t.arrival,
                "departure": t.departure,
                "scheduled": t.scheduled or t.arrival,
                "actual_arrival": t.actual_arrival or t.arrival,
                "priority": t.priority,
                "platform": t.platform,
                "status": t.status,
                "delay_minutes": int(t.delay_minutes or 0)
            }
            
            # Include explanation if available
            if t.explanation:
                train_dict["explanation"] = t.explanation
                
            trains.append(train_dict)

        # Sort trains by arrival time
        trains = sort_trains_by_arrival(trains)

        return {
            "date": schedule.date,
            "version": schedule.version,
            "trains": trains,
            "created_at": schedule.created_at.isoformat() if schedule.created_at else None,
            "updated_at": schedule.updated_at.isoformat() if schedule.updated_at else None,
            "notes": schedule.notes
        }
        
    except SQLAlchemyError as e:
        logger.exception(f"Database error while reading schedule: {e}")
        raise
    except Exception as e:
        logger.exception(f"Unexpected error while reading schedule: {e}")
        raise
