"""
Database connection for PostgreSQL (mobile database).
Reads DATABASE_URL from .env, or builds from DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD.
"""
import os
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, DateTime, ForeignKey, create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv

load_dotenv()


def _get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        if "psycopg2" in url:
            url = url.replace("psycopg2", "psycopg", 1)
        return url
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "mobile")
    user = os.getenv("DB_USER", "systemiser")
    password = os.getenv("DB_PASSWORD", "systemiser")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}"


DATABASE_URL = _get_database_url()

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class PKMixin:
    id = Column(Integer, primary_key=True, autoincrement=True)


class TimestampMixin:
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))


class TenantMixin:
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=True)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_connection():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True, None
    except Exception as e:
        return False, str(e)
