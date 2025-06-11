import random
from src.coach.models_db import WODModel
from src.coach.database import db_session


def create_wod_for_user(user_id: str, date: str):
    """
    Create and save a WOD for the specified user and date.
    Simulates a 20% chance of failure to test retry mechanisms.
    """
    
    wod_description = f"WOD for user {user_id} on {date}"

    wod = WODModel(user_id=user_id, date=date, description=wod_description)

    db = db_session()
    try:
        db.add(wod)
        db.commit()
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()
