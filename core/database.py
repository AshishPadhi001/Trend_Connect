from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from configuration.config import settings  # Import settings instead of DATABASE_URL

# Use settings to get the database URL
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Create the engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# Create the local session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
