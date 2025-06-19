from pydantic import BaseModel

class WorkoutStatSchema(BaseModel):
    user_id: str
    workout_id: str
