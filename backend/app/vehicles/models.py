"""Vehicle and VehicleImage models."""
from datetime import date, datetime
from sqlalchemy import Column, Integer, String, Text, Numeric, Date, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base, PKMixin, TimestampMixin


class Vehicle(PKMixin, TimestampMixin, Base):
    __tablename__ = "vehicles"

    name = Column(String(255), nullable=False)
    description = Column(Text)
    account_id = Column(Integer, ForeignKey("accounts.id", ondelete="CASCADE"), nullable=False)
    product = Column(String(20), nullable=False)  # car, bike, ev
    amount = Column(Numeric(12, 2), nullable=False)
    mileage = Column(Integer)
    location = Column(String(255))
    posting_date = Column(Date)
    model_year = Column(Integer, nullable=False)
    status = Column(String(20), nullable=False, default="active")  # active, sold, inactive

    images = relationship("VehicleImage", back_populates="vehicle", cascade="all, delete-orphan")


class VehicleImage(PKMixin, TimestampMixin, Base):
    __tablename__ = "vehicle_images"

    vehicle_id = Column(Integer, ForeignKey("vehicles.id", ondelete="CASCADE"), nullable=False)
    image_path = Column(String(500), nullable=False)

    vehicle = relationship("Vehicle", back_populates="images")
