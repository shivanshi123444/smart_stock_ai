import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. PRIORITY: Look for 'DATABASE_URL' set in Render Environment
# 2. FALLBACK: Only use localhost if DATABASE_URL is missing (for local testing)
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:password@localhost:5432/inventory_db")

# IMPORTANT FIX: Render/Heroku URLs often start with 'postgres://'
# SQLAlchemy 1.4+ REQUIRES 'postgresql://' to work correctly.
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Create the engine
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()