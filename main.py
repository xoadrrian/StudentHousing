import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from starlette.exceptions import HTTPException as StarletteHTTPException

import mqtt_listener
from database import DATABASE_URL, engine, get_db
from models import Base
from routers import auth, pages, sensors, tickets, inventory, chores
from routers.auth import HOME_BY_ROLE, get_current_user

if DATABASE_URL.startswith("sqlite"):
    Base.metadata.create_all(engine)


@asynccontextmanager
async def lifespan(app):
    client = mqtt_listener.start() if os.getenv("MQTT_HOST") else None
    yield
    if client:
        client.loop_stop()
        client.disconnect()


app = FastAPI(title="BV Housing", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(pages.router)
app.include_router(sensors.router)
app.include_router(tickets.router)
app.include_router(inventory.router)
app.include_router(chores.router)

if Path("static").is_dir():
    app.mount("/static", StaticFiles(directory="static"), name="static")


@app.exception_handler(StarletteHTTPException)
async def not_logged_in_goes_to_login(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 401 and "text/html" in request.headers.get("accept", ""):
        return RedirectResponse("/login")
    return await http_exception_handler(request, exc)


@app.get("/")
def root(request: Request, db: Session = Depends(get_db)):
    try:
        user = get_current_user(request, db)
    except HTTPException:
        return RedirectResponse("/login")
    return RedirectResponse(HOME_BY_ROLE[user.role])


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/health/mqtt")
def health_mqtt():
    if mqtt_listener.is_connected():
        return {"status": "ok"}
    return {"status": "disconnected"}