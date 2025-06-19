from datetime import datetime
from .models_db import WorkoutStat
from .database import db_session

from datetime import datetime

def save_workout_stat(message, db_session=None):
    from src.stats.database import db_session as default_db_session
    session = db_session or default_db_session

    stat = WorkoutStat(
        user_id=message["user_id"],
        workout_id=message["workout_id"],
        performed_at=datetime.fromisoformat(message["performed_at"]), 
    )
    session.add(stat)
    session.commit()



