"""
main.py - starts the app and connects all the parts.

Run it with:  fastapi dev main.py   then open http://127.0.0.1:8000
"""
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.exception_handlers import http_exception_handler
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from database import engine
from models import Base
from routers import auth

# Creates any missing tables. Fine for now; later the team may switch to migrations.
Base.metadata.create_all(engine)

app = FastAPI(title="BV Housing")

if Path("static").is_dir():
    app.mount("/static", StaticFiles(directory="static"), name="static")

app.include_router(auth.router)
# Teammates add theirs here, e.g. app.include_router(tickets.router)


@app.exception_handler(StarletteHTTPException)
async def not_logged_in_goes_to_login(request: Request, exc: StarletteHTTPException):
    """A browser hitting a protected page without logging in gets sent to /login."""
    if exc.status_code == 401 and "text/html" in request.headers.get("accept", ""):
        return RedirectResponse("/login")
    return await http_exception_handler(request, exc)


@app.get("/")
def root():
    return RedirectResponse("/login")
