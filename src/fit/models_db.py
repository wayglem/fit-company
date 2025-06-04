from datetime import datetime
from sqlalchemy import Column, DateTime, String, Float, Integer, Boolean, ForeignKey, Table, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from .database import Base

class UserModel(Base):
    __tablename__ = "users"

    email = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    role = Column(String, nullable=False)
    password_hash = Column(String, nullable=False)
    
    weight = Column(Float, nullable=True)
    height = Column(Float, nullable=True)
    fitness_goal = Column(String, nullable=True)
    onboarded = Column(String, default="false", nullable=False)

    def __repr__(self):
        return f"<User(email='{self.email}', name='{self.name}', role='{self.role}')>"

exercise_muscle_groups = Table(
    "exercise_muscle_groups",
    Base.metadata,
    Column("exercise_id", Integer, ForeignKey("exercises.id", ondelete="CASCADE"), primary_key=True),
    Column("muscle_group_id", Integer, ForeignKey("muscle_groups.id", ondelete="CASCADE"), primary_key=True),
    Column("is_primary", Boolean, default=False, nullable=False),
)
class WODHistoryModel(Base):
    __tablename__ = "wod_history"

    id = Column(Integer, primary_key=True, index=True)
    user_email = Column(String, ForeignKey("users.email"), nullable=False)
    exercise_id = Column(Integer, ForeignKey("exercises.id"), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)

    user = relationship("UserModel", backref="wod_entries")
    exercise = relationship("ExerciseModel")

    # Add this line:
    exercises = relationship(
        "ExerciseModel",
        secondary="wod_exercises",
        back_populates="wods"
    )

    def __repr__(self):
        return f"<WODHistory(user='{self.user_email}', exercise_id={self.exercise_id}, timestamp={self.timestamp})>"

class WODExerciseModel(Base):
    __tablename__ = "wod_exercises"

    wod_id = Column(Integer, ForeignKey("wod_history.id", ondelete="CASCADE"), primary_key=True)
    exercise_id = Column(Integer, ForeignKey("exercises.id", ondelete="CASCADE"), primary_key=True)

    wod = relationship("WODHistoryModel", backref="wod_exercise_links")
    exercise = relationship("ExerciseModel", backref="wod_exercise_links")

    def __repr__(self):
        return f"<WODExercise(wod_id={self.wod_id}, exercise_id={self.exercise_id})>"
class MuscleGroupModel(Base):
    __tablename__ = "muscle_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    body_part = Column(String(50), nullable=False)
    description = Column(Text)
    
    exercises = relationship(
        "ExerciseModel", 
        secondary=exercise_muscle_groups,
        back_populates="muscle_groups"
    )

    def __repr__(self):
        return f"<MuscleGroup(id={self.id}, name='{self.name}', body_part='{self.body_part}')>"

class ExerciseModel(Base):
    __tablename__ = "exercises"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    description = Column(Text)
    difficulty = Column(Integer, nullable=False)
    equipment = Column(String(100))
    instructions = Column(Text)
    
    muscle_groups = relationship(
        "MuscleGroupModel",
        secondary=exercise_muscle_groups,
        back_populates="exercises"
    )
    wods = relationship(
        "WODHistoryModel",
        secondary="wod_exercises",
        back_populates="exercises"
    )

    def __repr__(self):
        return f"<Exercise(id={self.id}, name='{self.name}', difficulty={self.difficulty})>" 