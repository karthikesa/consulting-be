"""
FastAPI app for Rathinam (mobile DB + JWT auth).
Run: uvicorn main:app --reload --host 0.0.0.0
"""
from pathlib import Path

from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

from app.database import get_db, check_connection
from app.vehicles.models import Vehicle
from app.core.config import settings
from app.auth.routes import router as auth_router
from app.vehicles.routes import router as vehicles_router

app = FastAPI(
    title="Rathinam API",
    description="FastAPI + PostgreSQL (mobile) with JWT auth for mobile app",
)

# CORS - required for Expo Web and mobile app to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins (localhost, 127.0.0.1, your IP, etc.)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(vehicles_router)


@app.get("/")
def root():
    return {"message": "Rathinam API. Try /health or /db-check."}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/db-check")
def db_check():
    ok, error = check_connection()
    if ok:
        return {"database": "connected", "status": "ok"}
    return {"database": "error", "message": error}


@app.get("/db-session-test")
def db_session_test(db: Session = Depends(get_db)):
    from sqlalchemy import text
    try:
        result = db.execute(text("SELECT current_database(), current_user"))
        row = result.fetchone()
        return {"database": row[0], "user": row[1], "message": "Database session works."}
    except Exception as e:
        return {"error": str(e)}


@app.get("/v/{vehicle_id}", response_class=HTMLResponse)
def vehicle_share_page(vehicle_id: int, request: Request, db: Session = Depends(get_db)):
    """Public shareable page: view vehicle details in browser (for WhatsApp link)."""
    from view.product import render_product_page

    v = db.get(Vehicle, vehicle_id)
    if not v or v.status != "active":
        raise HTTPException(status_code=404, detail="Vehicle not found")
    base = str(request.base_url).rstrip("/")
    img_urls = [f"{base}/storage/{img.image_path}" for img in v.images] if v.images else []
    html_content = render_product_page(v, base, img_urls)
    return HTMLResponse(html_content)


# Serve uploaded vehicle images (mount last so it doesn't shadow other routes)
storage_path = Path(__file__).resolve().parent / settings.STORAGE_DIR
storage_path.mkdir(parents=True, exist_ok=True)
(storage_path / "vehicles").mkdir(parents=True, exist_ok=True)
app.mount("/storage", StaticFiles(directory=str(storage_path)), name="storage")
