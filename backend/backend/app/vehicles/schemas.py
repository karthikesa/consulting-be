"""Pydantic schemas for Vehicle API."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class VehicleImageOut(BaseModel):
    id: int
    vehicle_id: int
    image_path: str

    class Config:
        from_attributes = True


class VehicleCreate(BaseModel):
    name: str = Field(..., min_length=1)
    description: Optional[str] = None
    product: str = Field(..., pattern="^(car|bike|ev)$")
    amount: Decimal = Field(..., ge=0)
    mileage: Optional[int] = Field(None, ge=0)
    location: Optional[str] = None
    posting_date: Optional[date] = None
    model_year: int = Field(..., ge=1900, le=2100)


class VehicleUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = None
    product: Optional[str] = Field(None, pattern="^(car|bike|ev)$")
    amount: Optional[Decimal] = Field(None, ge=0)
    mileage: Optional[int] = Field(None, ge=0)
    location: Optional[str] = None
    posting_date: Optional[date] = None
    model_year: Optional[int] = Field(None, ge=1900, le=2100)
    status: Optional[str] = Field(None, pattern="^(active|sold|inactive)$")


class VehicleOut(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    account_id: int
    product: str
    amount: Decimal
    mileage: Optional[int] = None
    location: Optional[str] = None
    posting_date: Optional[date] = None
    model_year: int
    status: str
    images: list[VehicleImageOut] = []
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class VehicleListOut(BaseModel):
    total: int
    page: int
    per_page: int
    items: list[VehicleOut]


class ImageIdsToRemove(BaseModel):
    image_ids: list[int] = Field(default_factory=list)
