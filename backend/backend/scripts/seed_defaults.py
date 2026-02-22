"""
Seed default account and Administrator role after migrations.
Run from project root: python -m scripts.seed_defaults
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select
from app.database import SessionLocal
from app.auth.models import Account, Role


def seed_defaults():
    db = SessionLocal()
    try:
        acc = db.execute(select(Account).where(Account.slug == "hashagile")).scalars().first()
        if not acc:
            acc = Account(name="Default", slug="hashagile")
            db.add(acc)
            db.flush()
        account_id = acc.id

        role = db.execute(
            select(Role).where(Role.name == "Administrator", Role.account_id == account_id)
        ).scalars().first()
        if not role:
            db.add(Role(name="Administrator", account_id=account_id))
        db.commit()
        print("Default account 'hashagile' and role 'Administrator' are ready.")
    finally:
        db.close()


if __name__ == "__main__":
    seed_defaults()
