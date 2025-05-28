from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session

# Database connection settings from docker-compose.yml
SQLALCHEMY_DATABASE_URL = "postgresql://postgres:docker@localhost:5433/fit-db"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
db_session = scoped_session(SessionLocal)

Base = declarative_base()

# Dependency to get db session
def get_db():
    db = db_session()
    try:
        yield db
    finally:
        db.close()

def init_db():
    # Import all models here so they are registered with the metadata
    from .models_db import UserModel, MuscleGroupModel, ExerciseModel
    
    Base.metadata.create_all(bind=engine) 