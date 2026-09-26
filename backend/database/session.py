"""
WATERSCOPE Backend - Database Session & Engine Configuration
Supports PostgreSQL/PostGIS and SQLite with graceful fallback.
"""

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from backend.config import settings

Base = declarative_base()

is_sqlite = settings.DATABASE_URL.startswith("sqlite")
connect_args = {"check_same_thread": False} if is_sqlite else {}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    echo=False
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """FastAPI Dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Create all tables in the database."""
    # Ensure foreign models are imported before creating tables
    import backend.database.models
    Base.metadata.create_all(bind=engine)
    print(f"[DATABASE] Initialized tables successfully on {settings.DATABASE_URL.split('@')[-1]}")
