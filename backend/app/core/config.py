"""App settings from environment variables."""
import os
from dotenv import load_dotenv

load_dotenv()


def _get_database_url() -> str:
    url = os.getenv("DATABASE_URL")
    if url:
        # Use psycopg (v3) driver; project has psycopg, not psycopg2
        if "psycopg2" in url:
            url = url.replace("psycopg2", "psycopg", 1)
        return url
    # Build from parts (same as app.database)
    user = os.getenv("DB_USER", "systemiser")
    password = os.getenv("DB_PASSWORD", "systemiser")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "mobile")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}"


class Settings:
    DATABASE_URL: str = _get_database_url()
    JWT_SECRET_KEY: str = os.getenv("JWT_SECRET_KEY", "change-me-in-production-use-long-secret")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    REFRESH_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("REFRESH_TOKEN_EXPIRE_MINUTES", "10080"))
    DEFAULT_ACCOUNT_SLUG: str = os.getenv("DEFAULT_ACCOUNT_SLUG", "hashagile")
    STORAGE_DIR: str = os.getenv("STORAGE_DIR", "storage")


settings = Settings()
