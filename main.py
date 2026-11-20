from contextlib import asynccontextmanager
<<<<<<< Updated upstream
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
from routers import auth, pages, sensors
from routers.auth import HOME_BY_ROLE, get_current_user
=======
from fastapi import FastAPI

import mqtt_listener
from routers import tickets
>>>>>>> Stashed changes

import mqtt_listener


@asynccontextmanager
async def lifespan(app):
    client = mqtt_listener.start()   # when the app starts
    yield
<<<<<<< Updated upstream
    if client:
        client.loop_stop()
        client.disconnect()


app = FastAPI(title="BV Housing", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(pages.router)
app.include_router(sensors.router)

if Path("static").is_dir():
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
=======
    client.loop_stop()               # when the app stops
    client.disconnect()

>>>>>>> Stashed changes

app = FastAPI(lifespan=lifespan)

<<<<<<< Updated upstream

@app.get("/")
def root(request: Request, db: Session = Depends(get_db)):
    try:
        user = get_current_user(request, db)
    except HTTPException:
        return RedirectResponse("/login")
    return RedirectResponse(HOME_BY_ROLE[user.role])
=======
app.include_router(tickets.router)
>>>>>>> Stashed changes


@app.get("/health")
def health():
    return {"status": "ok"}

<<<<<<< Updated upstream
@app.get("/health/mqtt")
def health_mqtt():
    if mqtt_listener.is_connected():
        return {"status": "ok"}
    return {"status": "disconnected"}
=======
>>>>>>> Stashed changes
