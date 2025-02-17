##Database.py

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from configuration.config import DATABASE_URL

#database url
SQLALCHEMY_DATABASE_URL = DATABASE_URL

#Create the engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

#Create the local session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

#Close Local session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
