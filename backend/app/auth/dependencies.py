"""Auth dependencies: OAuth2 scheme, get_current_user, roles_required."""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.config import settings
from app.core.security import decode_jwt, CLAIM_SUB, CLAIM_TYP, CLAIM_JTI
from app.auth.models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token", auto_error=True)


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_jwt(token, settings.JWT_SECRET_KEY)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if payload.get(CLAIM_TYP) != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type",
            headers={"WWW-Authenticate": "Bearer"},
        )
    from app.auth.service import is_revoked
    jti = payload.get(CLAIM_JTI)
    if jti and is_revoked(db, jti=jti):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has been revoked",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user_id = payload.get(CLAIM_SUB)
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = db.get(User, int(user_id))
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found or inactive")
    return user


def roles_required(*allowed_roles: str):
    def _check(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> User:
        from app.auth.service import get_user_roles
        roles = get_user_roles(db, user.id)
        if not any(r in roles for r in allowed_roles):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return user
    return _check
