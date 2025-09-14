#postgres_models.py
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class Schedule(Base):
    __tablename__ = "schedules"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, nullable=False)

    # One schedule -> many trains
    trains = relationship("TrainDB", back_populates="schedule", cascade="all, delete-orphan")


class TrainDB(Base):
    __tablename__ = "trains"
    id = Column(Integer, primary_key=True, index=True)

    # core fields
    train_id = Column(String, nullable=False)
    arrival = Column(String, nullable=False)
    departure = Column(String, nullable=False)

    # persisted front-end fields (new)
    scheduled = Column(String, nullable=True)       # optional "scheduled" display field
    actual_arrival = Column(String, nullable=True)  # actual arrival (when known)
    priority = Column(Integer, nullable=False)
    platform = Column(Integer, nullable=False)
    status = Column(String, nullable=True)          # e.g., "On time", "Delayed", "Cancelled"
    delay_minutes = Column(Integer, nullable=False, server_default="0")

    schedule_id = Column(Integer, ForeignKey("schedules.id"), nullable=False)
    schedule = relationship("Schedule", back_populates="trains")
