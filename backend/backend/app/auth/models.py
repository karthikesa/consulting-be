"""Auth models: Account, User, Role, UserRole."""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base, PKMixin, TimestampMixin, TenantMixin


class Account(PKMixin, TimestampMixin, Base):
    __tablename__ = "accounts"
    name = Column(String(200), nullable=False)
    slug = Column(String(80), unique=True, nullable=False, index=True)
    users = relationship("User", back_populates="account", cascade="all, delete-orphan")


class User(PKMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "users"
    email = Column(String(320), nullable=False, index=True)
    first_name = Column(String(200))
    last_name = Column(String(200))
    password_hash = Column(String(255))
    is_active = Column(Boolean, nullable=False, default=True)
    last_login_at = Column(DateTime(timezone=True))
    is_superuser = Column(Boolean, nullable=False, default=False)
    is_staff = Column(Boolean, nullable=False, default=False)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    account = relationship("Account", back_populates="users")
    roles = relationship("UserRole", back_populates="user", cascade="all, delete-orphan")


class Role(PKMixin, TenantMixin, TimestampMixin, Base):
    __tablename__ = "roles"
    name = Column(String(80), nullable=False)
    user_roles = relationship("UserRole", back_populates="role", cascade="all, delete-orphan")


class UserRole(PKMixin, Base):
    __tablename__ = "user_roles"
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="roles")
    role = relationship("Role", back_populates="user_roles")
