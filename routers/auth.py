"""
routers/auth.py - login, logout, and "who is this user?" for every other router.

How it works:
1. Login form posts email + password to POST /login.
2. We look up the user and check the password against the stored Argon2 hash.
3. If it matches, we put a signed token (a JWT) with the user's id and role in
   an httpOnly cookie. The browser sends that cookie with every request.
4. Other routes use `get_current_user` / `require_role(...)` to read the cookie.

Teammates only need this:
    from routers.auth import get_current_user, require_role

    @router.get("/manager/tickets")
    def all_tickets(user: User = Depends(require_role(Role.manager))):
        ...
"""
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

# --- Settings ---------------------------------------------------------------
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-secret-change-me-before-hosting-0000")
ALGORITHM = "HS256"
SESSION_HOURS = 8
COOKIE_NAME = "session"
# Only send the cookie over HTTPS once the site is hosted. Locally it's http.
COOKIE_SECURE = os.getenv("COOKIE_SECURE", "false").lower() == "true"

# Where each role lands after logging in. Teammates create these pages.
HOME_BY_ROLE = {
    Role.tenant: "/home",
    Role.manager: "/manager",
    Role.worker: "/worker",
}

# --- Passwords --------------------------------------------------------------
# Argon2 via pwdlib, the hasher FastAPI's own docs recommend. A hash can't be
# turned back into the password; we can only check if a password matches it.
password_hash = PasswordHash.recommended()

# Used when the email doesn't exist, so a wrong email takes as long as a wrong
# password. Otherwise an attacker could time responses to find real emails.
DUMMY_HASH = password_hash.hash("not-a-real-password")


def hash_password(plain: str) -> str:
    return password_hash.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return password_hash.verify(plain, hashed)


# --- Session token ----------------------------------------------------------
def create_session_token(user: User) -> str:
    """Signed token: anyone can read it, but nobody can change it without SECRET_KEY."""
    expires = datetime.now(timezone.utc) + timedelta(hours=SESSION_HOURS)
    payload = {"sub": str(user.user_id), "role": user.role.value, "exp": expires}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


# --- Dependencies other routers use -----------------------------------------
def get_current_user(request: Request, db: Session = Depends(get_db)) -> User:
    """Returns the logged-in user, or 401 (main.py turns that into a redirect to /login)."""
    token = request.cookies.get(COOKIE_NAME)
    if not token:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Not logged in")
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])  # also checks "exp"
        user_id = int(payload["sub"])
    except (jwt.InvalidTokenError, KeyError, ValueError):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Session invalid or expired")
    # Look the user up again instead of trusting the role in the token, so a
    # deleted user or a changed role takes effect straight away.
    user = db.get(User, user_id)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "User no longer exists")
    return user


def require_role(*allowed: Role):
    """Usage: Depends(require_role(Role.manager)) or require_role(Role.manager, Role.worker)."""
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed:
            raise HTTPException(status.HTTP_403_FORBIDDEN, "You don't have access to this page")
        return user
    return checker


# --- Routes -----------------------------------------------------------------
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

    # Always run one hash check, real or dummy (see DUMMY_HASH above).
    ok = verify_password(password, user.password_hash if user else DUMMY_HASH)
    if user is None or not ok:
        # Same message for wrong email and wrong password: don't reveal which.
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
        httponly=True,   # JavaScript can't read it, so XSS can't steal it
        samesite="lax",  # not sent on cross-site form posts (basic CSRF protection)
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
    """Quick test page: shows who you're logged in as."""
    return {"user_id": user.user_id, "name": f"{user.first_name} {user.surname}",
            "email": user.email, "role": user.role.value}
