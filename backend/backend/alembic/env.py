"""
Alembic env: use app.database engine and Base.metadata.
Run from project root: alembic upgrade head
"""
import os
import sys
from logging.config import fileConfig

from alembic import context

# Project root = parent of alembic/
_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)

# Load .env from project root before any app imports
_dotenv_path = os.path.join(_project_root, ".env")
if os.path.isfile(_dotenv_path):
    from dotenv import load_dotenv
    load_dotenv(_dotenv_path)

from app.database import Base, engine
from app.auth import models  # noqa: F401
from app.auth import models_extras  # noqa: F401
from app.vehicles import models as vehicle_models  # noqa: F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode (generate SQL only)."""
    url = str(engine.url)
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations using the same engine as the app (same .env credentials)."""
    with engine.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
