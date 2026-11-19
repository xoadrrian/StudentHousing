import os
import uuid
from datetime import datetime, timedelta, timezone

import httpx
import jwt
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from database import get_db
from models import Role, User

load_dotenv()

router = APIRouter()
templates = Jinja2Templates(directory="templates")

SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-change-me-before-hosting-0000")
ALGORITHM = "HS256"
SESSION_HOURS = 8
COOKIE_NAME = "session"

COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")

HOME_BY_ROLE = {
    Role.tenant: "/home",
    Role.manager: "/manager",
    Role.worker: "/worker",
}


class LoginServiceDown(Exception):
    pass


def supabase_sign_in(email: str, password: str) -> uuid.UUID | None:
    if not SUPABASE_URL or not SUPABASE_ANON_KEY:
        raise LoginServiceDown("SUPABASE_URL or SUPABASE_ANON_KEY missing in .env")
    try:
        r = httpx.post(
            f"{SUPABASE_URL}/auth/v1/token",
            params={"grant_type": "password"},
            headers={"apikey": SUPABASE_ANON_KEY},
            json={"email": email, "password": password},
            timeout=10,
        )
    except httpx.HTTPError as e:
        raise LoginServiceDown(str(e)) from e
    if r.status_code == 200:
        return uuid.UUID(r.json()["user"]["id"])
    if r.status_code in (400, 422):
        return None
    raise LoginServiceDown(f"Supabase Auth answered {r.status_code}")


def create_session_token(user: User) -> str:
    expires = datetime.now(timezone.utc) + timedelta(hours=SESSION_HOURS)
    payload = {"sub": str(user.id), "role": user.role.value, "exp": expires}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not logged in")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = uuid.UUID(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session invalid or expired")

    user = db.get(User, user_id)
    if user is None or user.role is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User no longer exists")
    return user


def require_role(*allowed: Role):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You don't have access to this page")
        return user
    return checker


def login_error(request: Request, message: str, code: int):
    return templates.TemplateResponse(request, "login.html", {"error": message}, status_code=code)


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None})


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        user_id = supabase_sign_in(email.strip().lower(), password)
    except LoginServiceDown:
        return login_error(request, "Login is unavailable right now. Try again later.",
                           status.HTTP_503_SERVICE_UNAVAILABLE)

    if user_id is None:
        return login_error(request, "Wrong email or password.", status.HTTP_401_UNAUTHORIZED)

    user = db.get(User, user_id)
    if user is None or user.role is None:
        return login_error(request, "Your account isn't set up yet. Contact the manager.",
                           status.HTTP_403_FORBIDDEN)

    response = RedirectResponse(HOME_BY_ROLE[user.role], status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(
        COOKIE_NAME,
        create_session_token(user),
        max_age=SESSION_HOURS * 3600,
        httponly=True,
        samesite="lax",
        secure=COOKIE_SECURE,
    )
    return response


@router.post("/logout")
def logout():
    response = RedirectResponse("/login", status_code=status.HTTP_303_SEE_OTHER)
    response.delete_cookie(COOKIE_NAME)
    return response


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return {"id": str(user.id), "name": f"{user.first_name} {user.last_name}",
            "email": user.email, "role": user.role.value}
