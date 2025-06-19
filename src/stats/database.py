from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from .models_db import Base

DATABASE_URL = "postgresql://postgres:docker@stats-db:5432/stats-db"


engine = create_engine(DATABASE_URL)
db_session = scoped_session(
    sessionmaker(autocommit=False, autoflush=False, bind=engine)
)


def init_db():
    import src.stats.models_db

    Base.metadata.create_all(bind=engine)
