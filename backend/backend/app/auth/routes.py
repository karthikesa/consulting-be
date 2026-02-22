"""Auth API routes for mobile app."""
from __future__ import annotations
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from app.database import get_db
from app.core.config import settings
from app.core.security import CLAIM_SUB, CLAIM_ACC, CLAIM_ROLE, CLAIM_TYP, CLAIM_JTI, decode_jwt, create_jwt, hash_password, verify_password
from app.auth.schemas import (
    RegisterRequest,
    VerifyEmailRequest,
    LoginRequest,
    TokenPair,
    RefreshRequest,
    UserOut,
    ForgotPasswordRequest,
    ResetPasswordRequest,
    ValidateTokenRequest,
)
from app.auth.service import (
    authenticate_user,
    issue_tokens,
    get_user_roles,
    register_user,
    verify_email,
    revoke_token,
    get_user_by_email,
    is_revoked,
)
from app.auth.dependencies import get_current_user, oauth2_scheme, roles_required
from app.auth.models import User

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> dict:
    try:
        user, verification_token = register_user(
            db, email=payload.email, password=payload.password,
            first_name=payload.first_name, last_name=payload.last_name,
            account_slug=payload.account_slug,
        )
        db.commit()
    except ValueError as e:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    return {"message": "Registered. Verify your email.", "verification_token": verification_token}


@router.post("/verify-email")
def verify(req: VerifyEmailRequest, db: Session = Depends(get_db)) -> dict:
    if not verify_email(db, req.token):
        db.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid/expired token")
    db.commit()
    return {"message": "Email verified"}


@router.post("/login", response_model=TokenPair)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenPair:
    user = authenticate_user(db, payload.email, payload.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    access, refresh = issue_tokens(user, get_user_roles(db, user.id))
    return TokenPair(access_token=access, refresh_token=refresh)


@router.post("/refresh", response_model=TokenPair)
def refresh(req: RefreshRequest, db: Session = Depends(get_db)) -> TokenPair:
    from app.core.security import create_jwt as _create
    try:
        data = decode_jwt(req.refresh_token, settings.JWT_SECRET_KEY)
        if data.get(CLAIM_TYP) != "refresh":
            raise ValueError("Not a refresh token")
        roles = get_user_roles(db, int(data[CLAIM_SUB]))
        new_access = _create(
            {CLAIM_SUB: data[CLAIM_SUB], CLAIM_ACC: data[CLAIM_ACC], CLAIM_ROLE: roles, CLAIM_TYP: "access"},
            settings.JWT_SECRET_KEY,
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        )
        return TokenPair(access_token=new_access, refresh_token=req.refresh_token)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")


@router.post("/logout")
def logout(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> dict:
    try:
        payload = decode_jwt(token, settings.JWT_SECRET_KEY)
        if payload.get(CLAIM_TYP) == "refresh":
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Use an access token, not refresh")
        jti = payload.get(CLAIM_JTI) or hashlib.sha256(token.encode("utf-8")).hexdigest()
        revoke_token(db, jti=jti, account_id=payload.get(CLAIM_ACC, 0), reason="logout", exp_ts=payload.get("exp"))
        db.commit()
        return {"message": "Logged out"}
    except HTTPException:
        raise
    except Exception:
        db.rollback()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> UserOut:
    return UserOut(
        id=user.id,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        account_id=user.account_id,
        roles=get_user_roles(db, user.id),
        is_superuser=user.is_superuser,
    )


@router.post("/token", response_model=TokenPair)
def login_token(form: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)) -> TokenPair:
    user = authenticate_user(db, form.username, form.password)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    access, refresh = issue_tokens(user, get_user_roles(db, user.id))
    return TokenPair(access_token=access, refresh_token=refresh)


@router.get("/admin/ping", dependencies=[Depends(roles_required("Administrator"))])
def admin_ping() -> dict:
    return {"ok": True}


@router.post("/forgot-password")
def forgot_password(payload: ForgotPasswordRequest, db: Session = Depends(get_db)) -> dict:
    out = {"message": "If the email exists, a reset link has been sent."}
    user = get_user_by_email(db, payload.email)
    if user:
        token = create_jwt({CLAIM_SUB: str(user.id), CLAIM_TYP: "reset"}, settings.JWT_SECRET_KEY, minutes=15)
        out["reset_token"] = token
    return out


@router.post("/reset-password")
def reset_password(payload: ResetPasswordRequest, db: Session = Depends(get_db)) -> dict:
    try:
        data = decode_jwt(payload.token, settings.JWT_SECRET_KEY)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    if data.get(CLAIM_TYP) != "reset":
        raise HTTPException(status_code=400, detail="Invalid token type")
    user_id = data.get(CLAIM_SUB)
    jti = data.get(CLAIM_JTI)
    if not user_id or not jti or is_revoked(db, jti=jti):
        raise HTTPException(status_code=400, detail="Invalid or already used token")
    user = db.get(User, int(user_id))
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if user.password_hash and verify_password(payload.new_password, user.password_hash):
        raise HTTPException(status_code=400, detail="New password cannot be the same as current")
    user.password_hash = hash_password(payload.new_password)
    revoke_token(db, jti=jti, account_id=user.account_id, reason="password_reset", exp_ts=data.get("exp"))
    db.commit()
    return {"message": "Password successfully reset"}


@router.post("/validate-reset-token")
def validate_reset_token(payload: ValidateTokenRequest, db: Session = Depends(get_db)) -> dict:
    try:
        data = decode_jwt(payload.token, settings.JWT_SECRET_KEY)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid or expired token")
    if data.get(CLAIM_TYP) != "reset":
        raise HTTPException(status_code=400, detail="Invalid token type")
    jti = data.get(CLAIM_JTI)
    if not jti or is_revoked(db, jti=jti):
        raise HTTPException(status_code=400, detail="Token already used or revoked")
    return {"valid": True}
