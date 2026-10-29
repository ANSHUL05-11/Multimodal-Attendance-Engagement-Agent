"""Database connection engine and session factory.

Configured with thread-safety for SQLite and clean session lifecycle management.
"""

from __future__ import annotations

import os
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session as DBSession, sessionmaker

from core.config import config, logger
from database.models import Base

# SQLite engine configuration
DATABASE_URL = os.getenv("DATABASE_URL", config.database_url)

# In SQLite, connect_args check_same_thread=False allows multi-threaded reads/writes in FastAPI & Streamlit
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, expire_on_commit=False, bind=engine)


def init_db() -> None:
    """Initialize database tables."""
    try:
        config.ensure_directories()
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully at %s", DATABASE_URL)
    except Exception as exc:
        logger.error("Failed to initialize database: %s", exc)
        raise


def get_db() -> Generator[DBSession, None, None]:
    """Dependency generator for FastAPI routes."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context() -> Generator[DBSession, None, None]:
    """Context manager for standalone scripts or Streamlit UI callbacks."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
