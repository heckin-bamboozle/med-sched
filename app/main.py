from fastapi import FastAPI, Request, Depends, Form, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from httpx import AsyncClient
from urllib.parse import urlencode
import os

from app.database import engine, get_db, Base
from app.models import User, Medication, DoseLog
from app.config import settings
from app.services.fda_api import search_drugs
from app.services.scheduler import scheduler

# Create Tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Family Med Tracker")

# Add Session Middleware for Login State
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

# Mount Static & Templates
app.mount("/static", StaticFiles(directory="app/static"), name="static")
templates = Jinja2Templates(directory="app/templates")

# Start Scheduler
scheduler.start()

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login")

    # Fetch user's meds
    meds = db.query(Medication).filter(Medication.owner_id == user['id']).all()

    # Calculate stats for template
    med_stats = []
    for m in meds:
        daily = m.pills_per_dose * m.doses_per_day
        days_left = m.current_count / daily if daily > 0 else 999
        med_stats.append({
            "med": m,
            "days_left": round(days_left, 1),
            "is_low": days_left <= m.alert_threshold_days
        })

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user": user,
        "medications": med_stats
    })

@app.get("/login")
async def login():
    params = {
        "client_id": settings.POCKET_ID_CLIENT_ID,
        "redirect_uri": settings.POCKET_ID_REDIRECT_URI,
        "response_type": "code",
        "scope": "openid profile email"
    }
    auth_url = f"{settings.POCKET_ID_ISSUER}/authorize?{urlencode(params)}"
    return RedirectResponse(url=auth_url)

@app.get("/callback")
async def callback(request: Request, code: str, db: Session = Depends(get_db)):
    # Exchange code for token
    async with AsyncClient() as client:
        try:
            token_resp = await client.post(
                f"{settings.POCKET_ID_ISSUER}/token",
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": settings.POCKET_ID_REDIRECT_URI,
                    "client_id": settings.POCKET_ID_CLIENT_ID,
                    "client_secret": settings.POCKET_ID_CLIENT_SECRET
                }
            )
            token_resp.raise_for_status()
            tokens = token_resp.json()

            # Get User Info
            user_resp = await client.get(
                f"{settings.POCKET_ID_ISSUER}/userinfo",
                headers={"Authorization": f"Bearer {tokens['access_token']}"}
            )
            user_resp.raise_for_status()
            userinfo = user_resp.json()

            sub = userinfo['sub']

            # Find or Create User
            user = db.query(User).filter(User.pocket_id_sub == sub).first()
            if not user:
                # First time login: Create user.
                # Logic: If no users exist, make this one admin. Otherwise regular user.
                is_admin = db.query(User).count() == 0
                user = User(
                    pocket_id_sub=sub,
                    name=userinfo.get('name', 'User'),
                    email=userinfo.get('email', ''),
                    is_admin=is_admin
                )
                db.add(user)
                db.commit()
                db.refresh(user)

            # Store in session
            request.session["user"] = {
                "id": user.id,
                "name": user.name,
                "is_admin": user.is_admin
            }
        except Exception as e:
            print(f"Auth Error: {e}")
            raise HTTPException(status_code=400, detail="Authentication failed")

    return RedirectResponse(url="/")

@app.get("/add-med", response_class=HTMLResponse)
async def add_med_page(request: Request, q: str = None, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user:
        return RedirectResponse(url="/login")

    results = []
    if q:
        results = await search_drugs(q)
    return templates.TemplateResponse("add_med.html", {"request": request, "results": results, "query": q})

@app.post("/save-med")
async def save_med(
    request: Request,
    brand_name: str = Form(...),
    generic_name: str = Form(...),
    ndc_code: str = Form(...),
    pills_per_dose: int = Form(...),
    doses_per_day: int = Form(...),
    current_count: int = Form(...),
    db: Session = Depends(get_db)
):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    new_med = Medication(
        owner_id=user['id'],
        brand_name=brand_name,
        generic_name=generic_name,
        ndc_code=ndc_code,
        pills_per_dose=pills_per_dose,
        doses_per_day=doses_per_day,
        current_count=current_count,
        initial_count=current_count
    )
    db.add(new_med)
    db.commit()
    return RedirectResponse(url="/", status_code=303)

@app.post("/log-dose/{med_id}")
async def log_dose(med_id: int, request: Request, db: Session = Depends(get_db)):
    user = request.session.get("user")
    if not user:
        raise HTTPException(status_code=401, detail="Not authenticated")

    med = db.query(Medication).filter(Medication.id == med_id).first()

    if not med:
        raise HTTPException(status_code=404, detail="Medication not found")

    # Decrement count
    if med.current_count >= med.pills_per_dose:
        med.current_count -= med.pills_per_dose

        # Log it
        log = DoseLog(medication_id=med.id, logged_by_id=user['id'], taken=True)
        db.add(log)
        db.commit()

    return RedirectResponse(url="/", status_code=303)

# PWA Manifest Endpoint
@app.get("/manifest.json")
async def manifest():
    return {
        "name": "Family Med Tracker",
        "short_name": "MedTrack",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#ffffff",
        "theme_color": "#3b82f6",
        "icons": [
            {
                "src": "/static/icons/icon-192.png",
                "sizes": "192x192",
                "type": "image/png"
            },
            {
                "src": "/static/icons/icon-512.png",
                "sizes": "512x512",
                "type": "image/png"
            }
        ]
    }
