from typing import List, Tuple
from ..models_db import ExerciseModel, MuscleGroupModel, exercise_muscle_groups
from ..database import db_session
import random
from time import time
from datetime import datetime, timedelta
from ..models_db import WODHistoryModel

def heavy_computation(duration_seconds: int = 3):
    """
    Perform CPU-intensive calculations to simulate heavy processing.
    Uses matrix operations which are CPU-intensive.
    """
    start_time = time()
    i = 0
    while (time() - start_time) < duration_seconds:
        j = 0
        while j < 1000000:
            j += 1
        i += 1

def calculate_intensity(difficulty: int) -> float:
    """
    Calculate the intensity of an exercise based on its difficulty level (1-5).
    Returns a value between 0.0 and 1.0.
    """
    return (difficulty - 1) / 4.0

from datetime import datetime, timedelta

def request_wod(email: str) -> List[Tuple[ExerciseModel, List[Tuple[MuscleGroupModel, bool]]]]:
    heavy_computation(random.randint(1, 5)) 
    db = db_session()
    try:
        today = datetime.utcnow().date()
        start_of_day = datetime.combine(today, datetime.min.time())
        start_of_next_day = start_of_day + timedelta(days=1)

        wod_entries = db.query(WODHistoryModel).filter(
            WODHistoryModel.user_email == email,
            WODHistoryModel.timestamp >= start_of_day,
            WODHistoryModel.timestamp < start_of_next_day,
        ).all()

        if wod_entries:
            exercise_ids = [entry.exercise_id for entry in wod_entries]
            exercises = db.query(ExerciseModel).filter(ExerciseModel.id.in_(exercise_ids)).all()
        else:
            all_exercises = db.query(ExerciseModel).all()
            exercises = random.sample(all_exercises, 6) if len(all_exercises) >= 6 else all_exercises

            for exercise in exercises:
                wod_entry = WODHistoryModel(
                    user_email=email,
                    exercise_id=exercise.id,
                    timestamp=datetime.utcnow()
                )
                db.add(wod_entry)
            db.commit()

        # Fetch muscle groups info for each exercise
        result = []
        for exercise in exercises:
            stmt = db.query(
                MuscleGroupModel,
                exercise_muscle_groups.c.is_primary
            ).join(
                exercise_muscle_groups,
                MuscleGroupModel.id == exercise_muscle_groups.c.muscle_group_id
            ).filter(
                exercise_muscle_groups.c.exercise_id == exercise.id
            )
            muscle_groups = [(mg, is_primary) for mg, is_primary in stmt.all()]
            result.append((exercise, muscle_groups))

        return result
    finally:
        db.close()
def get_recent_exercises(user_email: str, days: int = 7) -> List[int]:
    from ..database import db_session
    from ..models_db import WODHistoryModel
    from datetime import datetime, timedelta

    db = db_session()
    try:
        cutoff = datetime.utcnow() - timedelta(days=days)
        recent_entries = db.query(WODHistoryModel.exercise_id)\
            .filter(WODHistoryModel.user_email == user_email)\
            .filter(WODHistoryModel.timestamp >= cutoff)\
            .all()
        return [entry.exercise_id for entry in recent_entries]
    finally:
        db.close()


    