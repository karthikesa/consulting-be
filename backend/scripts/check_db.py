"""
Test database connection using the same .env as the app and Alembic.
Run from project root: python -m scripts.check_db

If this fails with "password authentication failed", fix DB_PASSWORD in .env
to match the password you use for: psql -U systemiser -d mobile
"""
import os
import sys

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, _project_root)

# Load .env from project root
env_path = os.path.join(_project_root, ".env")
if os.path.isfile(env_path):
    from dotenv import load_dotenv
    load_dotenv(env_path)
    print(f"Loaded .env from: {env_path}")
else:
    print(f"No .env file at {env_path} — using defaults (DB_PASSWORD=systemiser)")

from app.database import engine
from sqlalchemy import text

# Show what we're connecting to (no password)
url = engine.url
print(f"Connecting as: {url.username}@{url.host}:{url.port}/{url.database}")

try:
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    print("Connection OK. You can run: alembic upgrade head")
except Exception as e:
    print(f"Connection failed: {e}")
    print("\nFix: Create .env in the project root with the correct DB_PASSWORD.")
    print("  cp .env.example .env")
    print("  Then edit .env and set DB_PASSWORD to the password that works for:")
    print("  psql -U systemiser -d mobile")
