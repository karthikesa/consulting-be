# app/core/security.py
from __future__ import annotations

import hashlib
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict

import bcrypt
import jwt

# JWT algorithm and claim names (match old app; we use "role" not "roles" for payload key)
ALGO_HS256 = "HS256"
CLAIM_SUB = "sub"
CLAIM_EXP = "exp"
CLAIM_IAT = "iat"
CLAIM_JTI = "jti"
CLAIM_ACC = "acc"
CLAIM_ROLE = "role"
CLAIM_TYP = "typ"

# Bcrypt accepts up to 72 bytes. Pre-hash with SHA256 for longer passwords (no passlib – use bcrypt directly).
_MAX_BCRYPT_BYTES = 72


def _to_bcrypt_input(plain: str) -> bytes:
    s = (
        plain
        if len(plain.encode("utf-8")) <= _MAX_BCRYPT_BYTES
        else hashlib.sha256(plain.encode("utf-8")).hexdigest()
    )
    return s.encode("utf-8")


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(_to_bcrypt_input(plain), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_to_bcrypt_input(plain), hashed.encode("utf-8"))
    except Exception:
        return False


def _with_std_claims(payload: Dict[str, Any], minutes: int, jti: str | None = None) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    return {
        CLAIM_IAT: int(now.timestamp()),
        CLAIM_EXP: int((now + timedelta(minutes=minutes)).timestamp()),
        CLAIM_JTI: jti or uuid.uuid4().hex,
        **payload,
    }


def create_jwt(payload: Dict[str, Any], secret: str, minutes: int = 60, jti: str | None = None) -> str:
    data = _with_std_claims(payload, minutes, jti=jti)
    return jwt.encode(data, secret, algorithm=ALGO_HS256)


def decode_jwt(token: str, secret: str) -> Dict[str, Any]:
    return jwt.decode(token, secret, algorithms=[ALGO_HS256])
