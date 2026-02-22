# db/migrations/session.py – uses DATABASE_URL from .env (see app.core.config)
from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

# Sync engine using DATABASE_URL from .env (postgresql+psycopg:// or postgresql+psycopg2://)
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
)

SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
)

def get_db():
    """FastAPI dependency that yields a DB session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
