import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

import mqtt_listener
from database import DATABASE_URL, engine
from models import Base
from routers import auth, pages

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

if Path("static").is_dir():
    app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router)


@app.exception_handler(StarletteHTTPException)
async def not_logged_in_goes_to_login(request: Request, exc: StarletteHTTPException):
    if exc.status_code == 401 and "text/html" in request.headers.get("accept", ""):
        return RedirectResponse("/login")
    return await http_exception_handler(request, exc)


@app.get("/")
def root():
    return RedirectResponse("/login")


@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/health/mqtt")
def health_mqtt():
    if mqtt_listener.is_connected():
        return {"status": "ok"}
    return {"status": "disconnected"}

app.include_router(pages.router)
