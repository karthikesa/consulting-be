"""Email verification and token blocklist."""
from datetime import datetime, timezone, timedelta
import secrets
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from app.database import Base, PKMixin, TimestampMixin, TenantMixin


class EmailVerification(PKMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "email_verifications"
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(String(255), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    is_used = Column(Boolean, nullable=False, default=False)

    @staticmethod
    def new_token() -> str:
        return secrets.token_urlsafe(32)

    @staticmethod
    def default_expiry(minutes: int = 60) -> datetime:
        return datetime.now(timezone.utc) + timedelta(minutes=minutes)


class TokenBlocklist(PKMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "token_blocklist"
    jti = Column(String(255), nullable=False, unique=True, index=True)
    reason = Column(String(80))
    expires_at = Column(DateTime(timezone=True))
