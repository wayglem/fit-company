from time import time
from ..database import db_session
from ..models_db import (
    WODHistoryModel, ExerciseModel, WODExerciseModel, MuscleGroupModel, exercise_muscle_groups
)
from ..models_dto import WOD, Exercise
from datetime import datetime, timedelta
from typing import List, Tuple
import random

class WODService:
    @staticmethod
    def request_wod(email: str) -> List[Tuple[ExerciseModel, List[Tuple[MuscleGroupModel, bool]]]]:
        """
        Generate or retrieve today's WOD for a specific user based on email.
        Returns a list of (Exercise, [(MuscleGroup, is_primary)]) tuples.
        """
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
    

def get_all_wods():
    db = db_session()
    try:
        wods = db.query(WODHistoryModel).all()
        result = []
        for wod in wods:
            wod_exercises = db.query(ExerciseModel).join(
                WODExerciseModel,
                (WODExerciseModel.exercise_id == ExerciseModel.id) & (WODExerciseModel.wod_id == wod.id)
            ).all()

            exercises_dto = [
                Exercise.model_validate({
                    "id": ex.id,
                    "name": ex.name,
                    "description": ex.description,
                    "difficulty": ex.difficulty,
                    "equipment": ex.equipment,
                    "instructions": ex.instructions,
                    "muscle_groups": []
                })
                for ex in wod_exercises
            ]

            result.append(WOD.model_validate({
                "id": wod.id,
                "name": wod.name,
                "description": wod.description,
                "created_at": wod.created_at,
                "exercises": exercises_dto
            }))
        return result
    finally:
        db.close()


def get_wod_by_id(wod_id: int):
    db = db_session()
    try:
        wod = db.query(WODHistoryModel).filter(WODHistoryModel.id == wod_id).first()
        if not wod:
            return None

        wod_exercises = db.query(ExerciseModel).join(
            WODExerciseModel,
            (WODExerciseModel.exercise_id == ExerciseModel.id) & (WODExerciseModel.wod_id == wod.id)
        ).all()

        exercises_dto = [
            Exercise.model_validate({
                "id": ex.id,
                "name": ex.name,
                "description": ex.description,
                "difficulty": ex.difficulty,
                "equipment": ex.equipment,
                "instructions": ex.instructions,
                "muscle_groups": []
            })
            for ex in wod_exercises
        ]

        return WOD.model_validate({
            "id": wod.id,
            "name": wod.name,
            "description": wod.description,
            "created_at": wod.created_at,
            "exercises": exercises_dto
        })
    finally:
        db.close()


def create_wod(wod_data: WOD):
    db = db_session()
    try:
        new_wod = WODHistoryModel(
            name=wod_data.name,
            description=wod_data.description,
            created_at=datetime.utcnow()
        )
        db.add(new_wod)
        db.flush()

        for ex in wod_data.exercises:
            db.add(WODExerciseModel(
                wod_id=new_wod.id,
                exercise_id=ex.id
            ))
        db.commit()
        return get_wod_by_id(new_wod.id)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def update_wod(wod_id: int, wod_data: WOD):
    db = db_session()
    try:
        wod = db.query(WODHistoryModel).filter(WODHistoryModel.id == wod_id).first()
        if not wod:
            return None

        wod.name = wod_data.name
        wod.description = wod_data.description

        db.query(WODExerciseModel).filter(WODExerciseModel.wod_id == wod_id).delete()

        for ex in wod_data.exercises:
            db.add(WODExerciseModel(
                wod_id=wod_id,
                exercise_id=ex.id
            ))
        db.commit()
        return get_wod_by_id(wod_id)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def delete_wod(wod_id: int):
    db = db_session()
    try:
        db.query(WODExerciseModel).filter(WODExerciseModel.wod_id == wod_id).delete()
        deleted = db.query(WODHistoryModel).filter(WODHistoryModel.id == wod_id).delete()
        db.commit()
        return deleted > 0
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
