from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, DateTime
from datetime import datetime

Base = declarative_base()

class WorkoutStat(Base):
    __tablename__ = "workout_stats"

    id = Column(Integer, primary_key=True)
    user_id = Column(String, nullable=False)
    workout_id = Column(String, nullable=False)
    performed_at = Column(DateTime, default=datetime.utcnow)
