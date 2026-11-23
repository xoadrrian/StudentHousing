from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session

import mqtt_listener

from database import get_db
from routers import auth, pages, sensors, tickets
from routers.auth import HOME_BY_ROLE, get_current_user


@asynccontextmanager
async def lifespan(app: FastAPI):
    client = mqtt_listener.start()

    yield

    if client:
        client.loop_stop()
        client.disconnect()


app = FastAPI(
    title="BV Housing",
    lifespan=lifespan
)

print("AUTH ROUTER LOADED")

# Routers
app.include_router(auth.router)
app.include_router(pages.router)
app.include_router(sensors.router)
app.include_router(tickets.router)

# Static files
if Path("static").is_dir():
    app.mount("/static", StaticFiles(directory="static"), name="static")


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
    return {
        "status": "ok" if mqtt_listener.is_connected() else "disconnected"
    }