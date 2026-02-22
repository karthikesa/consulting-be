"""Auth business logic: register, verify, login, tokens, revocation."""
from __future__ import annotations
from typing import Optional, Tuple, List

from sqlalchemy.orm import Session
from sqlalchemy import select, join
from datetime import datetime, timezone

from app.core.config import settings
from app.core.security import (
    create_jwt,
    verify_password,
    hash_password,
    CLAIM_SUB,
    CLAIM_ACC,
    CLAIM_ROLE,
    CLAIM_TYP,
)
from app.auth.models import User, Role, UserRole, Account
from app.auth.models_extras import EmailVerification, TokenBlocklist


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.execute(select(User).where(User.email == email)).scalars().first()


def get_user_roles(db: Session, user_id: int) -> List[str]:
    j = join(UserRole, Role, UserRole.role_id == Role.id)
    stmt = select(Role.name).select_from(j).where(UserRole.user_id == user_id)
    return [r[0] for r in db.execute(stmt).all()]


def find_account_id(db: Session, slug: str) -> Optional[int]:
    row = db.execute(select(Account.id).where(Account.slug == slug)).scalars().first()
    return int(row) if row is not None else None


def register_user(
    db: Session,
    *,
    email: str,
    password: str,
    first_name: Optional[str],
    last_name: Optional[str],
    account_slug: str,
) -> Tuple[User, str]:
    if get_user_by_email(db, email):
        raise ValueError("Email already registered")
    account_id = find_account_id(db, account_slug)
    if not account_id:
        raise ValueError("Invalid account")
    user = User(
        email=email,
        password_hash=hash_password(password),
        first_name=first_name,
        last_name=last_name,
        is_active=True,
        is_staff=False,
        is_superuser=False,
        account_id=account_id,
    )
    db.add(user)
    db.flush()
    token_str = EmailVerification.new_token()
    ev = EmailVerification(
        account_id=account_id,
        user_id=user.id,
        token=token_str,
        expires_at=EmailVerification.default_expiry(60),
        is_used=False,
    )
    db.add(ev)
    return user, token_str


def verify_email(db: Session, token_str: str) -> bool:
    now = datetime.now(timezone.utc)
    ev = db.execute(select(EmailVerification).where(EmailVerification.token == token_str)).scalars().first()
    if not ev or ev.is_used or ev.expires_at < now:
        return False
    user = db.get(User, ev.user_id)
    if not user:
        return False
    user.is_staff = True
    ev.is_used = True
    return True


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user or not user.is_active:
        return None
    if not verify_password(password, user.password_hash or ""):
        return None
    return user


def issue_tokens(user: User, roles: List[str]) -> Tuple[str, str]:
    sub = str(user.id)
    access_payload = {CLAIM_SUB: sub, CLAIM_ACC: user.account_id, CLAIM_ROLE: roles, CLAIM_TYP: "access"}
    refresh_payload = {CLAIM_SUB: sub, CLAIM_ACC: user.account_id, CLAIM_TYP: "refresh"}
    access = create_jwt(access_payload, settings.JWT_SECRET_KEY, minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    refresh = create_jwt(refresh_payload, settings.JWT_SECRET_KEY, minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
    return access, refresh


def revoke_token(db: Session, *, jti: str, account_id: int, reason: str | None, exp_ts: int | None) -> None:
    expires_at = datetime.fromtimestamp(exp_ts, tz=timezone.utc) if exp_ts else None
    db.add(TokenBlocklist(account_id=account_id, jti=jti, reason=reason, expires_at=expires_at))


def is_revoked(db: Session, *, jti: str) -> bool:
    return db.execute(select(TokenBlocklist.id).where(TokenBlocklist.jti == jti)).scalars().first() is not None
