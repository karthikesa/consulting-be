"""Vehicle CRUD API with multi-tenant and image upload."""
import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.database import get_db
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.core.config import settings
from app.vehicles.models import Vehicle, VehicleImage
from app.vehicles.schemas import (
    VehicleCreate,
    VehicleUpdate,
    VehicleOut,
    VehicleListOut,
    VehicleImageOut,
    ImageIdsToRemove,
)

router = APIRouter(prefix="/vehicles", tags=["Vehicles"])

ALLOWED_EXTENSIONS = {"jpeg", "jpg", "png", "webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


def _ensure_upload_dir() -> Path:
    base = Path(settings.STORAGE_DIR) / "vehicles"
    base.mkdir(parents=True, exist_ok=True)
    return base


def _save_image(file: UploadFile) -> str:
    ext = file.filename.split(".")[-1].lower() if file.filename else "jpg"
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid image type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}",
        )
    content = file.file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image too large. Max 5MB.",
        )
    base = _ensure_upload_dir()
    name = f"{uuid.uuid4().hex}.{ext}"
    path = base / name
    path.write_bytes(content)
    return f"vehicles/{name}"


def _vehicle_to_out(v: Vehicle) -> VehicleOut:
    return VehicleOut(
        id=v.id,
        name=v.name,
        description=v.description,
        account_id=v.account_id,
        product=v.product,
        amount=v.amount,
        mileage=v.mileage,
        location=v.location,
        posting_date=v.posting_date,
        model_year=v.model_year,
        status=v.status,
        images=[VehicleImageOut(id=img.id, vehicle_id=img.vehicle_id, image_path=img.image_path) for img in v.images],
        created_at=v.created_at,
        updated_at=v.updated_at,
    )


def _get_vehicle_or_404(db: Session, vehicle_id: int, account_id: int) -> Vehicle:
    v = db.get(Vehicle, vehicle_id)
    if not v or v.account_id != account_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    return v


@router.post("", status_code=status.HTTP_201_CREATED)
def create_vehicle(
    name: str = Form(...),
    description: str | None = Form(None),
    product: str = Form(...),
    amount: float = Form(...),
    mileage: int | None = Form(None),
    location: str | None = Form(None),
    posting_date: str | None = Form(None),
    model_year: int = Form(...),
    images: list[UploadFile] | None = File(None),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Create vehicle with multiple images."""
    from datetime import datetime
    from decimal import Decimal
    posting_d = None
    if posting_date:
        try:
            posting_d = datetime.strptime(posting_date, "%Y-%m-%d").date()
        except ValueError:
            pass
    payload = VehicleCreate(
        name=name.strip() if name else "",
        description=description.strip() if description else None,
        product=product.lower(),
        amount=Decimal(str(amount)),
        mileage=mileage,
        location=location.strip() if location else None,
        posting_date=posting_d,
        model_year=model_year,
    )
    vehicle = Vehicle(
        name=payload.name,
        description=payload.description,
        account_id=user.account_id,
        product=payload.product,
        amount=payload.amount,
        mileage=payload.mileage,
        location=payload.location,
        posting_date=payload.posting_date,
        model_year=payload.model_year,
        status="active",
    )
    db.add(vehicle)
    db.flush()
    for img in (images or []):
        if img.filename:
            path = _save_image(img)
            db.add(VehicleImage(vehicle_id=vehicle.id, image_path=path))
    db.commit()
    db.refresh(vehicle)
    return _vehicle_to_out(vehicle)


@router.get("/browse", response_model=VehicleListOut)
def browse_vehicles(
    page: int = 1,
    per_page: int = 20,
    product: str | None = None,
    db: Session = Depends(get_db),
):
    """Public: browse all active vehicles (for mobile app home/guest users)."""
    q = db.query(Vehicle).filter(Vehicle.status == "active")
    if product and product in ("car", "bike", "ev"):
        q = q.filter(Vehicle.product == product)
    total = q.count()
    items = q.order_by(Vehicle.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return VehicleListOut(
        total=total,
        page=page,
        per_page=per_page,
        items=[_vehicle_to_out(v) for v in items],
    )


@router.get("", response_model=VehicleListOut)
def list_vehicles(
    page: int = 1,
    per_page: int = 20,
    product: str | None = None,
    status_filter: str | None = None,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """List vehicles for the logged-in user's account. Filter by product and status."""
    q = db.query(Vehicle).filter(Vehicle.account_id == user.account_id)
    if product and product in ("car", "bike", "ev"):
        q = q.filter(Vehicle.product == product)
    if status_filter and status_filter in ("active", "sold", "inactive"):
        q = q.filter(Vehicle.status == status_filter)
    total = q.count()
    items = q.order_by(Vehicle.created_at.desc()).offset((page - 1) * per_page).limit(per_page).all()
    return VehicleListOut(
        total=total,
        page=page,
        per_page=per_page,
        items=[_vehicle_to_out(v) for v in items],
    )


@router.get("/browse/{vehicle_id}", response_model=VehicleOut)
def get_vehicle_public(
    vehicle_id: int,
    db: Session = Depends(get_db),
):
    """Public: get a single active vehicle by ID (for detail page)."""
    v = db.get(Vehicle, vehicle_id)
    if not v or v.status != "active":
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vehicle not found")
    return _vehicle_to_out(v)


@router.get("/{vehicle_id}", response_model=VehicleOut)
def get_vehicle(
    vehicle_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Get a single vehicle by ID."""
    v = _get_vehicle_or_404(db, vehicle_id, user.account_id)
    return _vehicle_to_out(v)


@router.patch("/{vehicle_id}", response_model=VehicleOut)
def update_vehicle(
    vehicle_id: int,
    payload: VehicleUpdate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Update vehicle. Use separate endpoints to add/remove images."""
    v = _get_vehicle_or_404(db, vehicle_id, user.account_id)
    data = payload.model_dump(exclude_unset=True)
    for k, val in data.items():
        setattr(v, k, val)
    db.commit()
    db.refresh(v)
    return _vehicle_to_out(v)


@router.post("/{vehicle_id}/images")
def add_vehicle_images(
    vehicle_id: int,
    images: list[UploadFile] = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Add images to an existing vehicle."""
    v = _get_vehicle_or_404(db, vehicle_id, user.account_id)
    for img in images:
        if img.filename:
            path = _save_image(img)
            db.add(VehicleImage(vehicle_id=v.id, image_path=path))
    db.commit()
    db.refresh(v)
    return _vehicle_to_out(v)


@router.delete("/{vehicle_id}/images")
def remove_vehicle_images(
    vehicle_id: int,
    payload: ImageIdsToRemove,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove specific images from a vehicle."""
    v = _get_vehicle_or_404(db, vehicle_id, user.account_id)
    storage_root = Path(settings.STORAGE_DIR)
    for img in v.images:
        if img.id in payload.image_ids:
            full_path = storage_root / img.image_path
            if full_path.exists():
                full_path.unlink()
            db.delete(img)
    db.commit()
    db.refresh(v)
    return _vehicle_to_out(v)


@router.delete("/{vehicle_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vehicle(
    vehicle_id: int,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Delete vehicle and its images."""
    v = _get_vehicle_or_404(db, vehicle_id, user.account_id)
    storage_root = Path(settings.STORAGE_DIR)
    for img in v.images:
        full_path = storage_root / img.image_path
        if full_path.exists():
            full_path.unlink()
    db.delete(v)
    db.commit()
