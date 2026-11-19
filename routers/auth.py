import os
from datetime import datetime, timedelta, timezone

import jwt
from dotenv import load_dotenv
from fastapi import APIRouter, Depends, Form, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pwdlib import PasswordHash
from sqlalchemy import select
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

HOME_BY_ROLE = {
    Role.tenant: "/home",
    Role.manager: "/manager",
    Role.worker: "/worker",
}

password_hash = PasswordHash.recommended()

DUMMY_HASH = password_hash.hash("not-a-real-password")


def hash_password(plain: str) -> str:
    return password_hash.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return password_hash.verify(plain, hashed)


def create_session_token(user: User) -> str:
    expires = datetime.now(timezone.utc) + timedelta(hours=SESSION_HOURS)
    payload = {"sub": str(user.user_id), "role": user.role.value, "exp": expires}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not logged in")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session invalid or expired")

    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User no longer exists")
    return user


def require_role(*allowed: Role):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You don't have access to this page")
        return user
    return checker


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request, "index.html", {"error": None})


@router.post("/login")
def login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    user = db.scalar(select(User).where(User.email == email.strip().lower()))

    ok = verify_password(password, user.password_hash if user else DUMMY_HASH)
    if user is None or not ok:

        return templates.TemplateResponse(
            request, "index.html",
            {"error": "Wrong email or password."},
            status_code=status.HTTP_401_UNAUTHORIZED,
        )

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
    return {"user_id": user.user_id, "name": f"{user.first_name} {user.surname}",
            "email": user.email, "role": user.role.value}
