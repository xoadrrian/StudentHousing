"""
Tests for login, logout and role checks (routers/auth.py).

Run from the project folder:   python -m pytest -v

Each test gets a fresh, empty database that lives only in memory, so tests
never touch local.db or Supabase and can't affect each other.
"""
import base64
import json

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database import get_db
from main import app
from models import Base, Role, User
from routers.auth import COOKIE_NAME, hash_password, require_role

PASSWORD = "Test1234!"


# A fake protected page, only for testing require_role.
@app.get("/test-manager-only")
def manager_only(user: User = Depends(require_role(Role.manager))):
    return {"ok": True}


@pytest.fixture
def client():
    # In-memory SQLite. StaticPool keeps one connection so all requests see the same data.
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)

    with TestSession() as db:
        db.add_all([
            User(first_name="Emma", surname="Johnson", email="tenant@test.com",
                 password_hash=hash_password(PASSWORD), role=Role.tenant),
            User(first_name="John", surname="Doe", email="manager@test.com",
                 password_hash=hash_password(PASSWORD), role=Role.manager),
        ])
        db.commit()

    def get_test_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    # Swap the real database for the test one, only while this test runs.
    app.dependency_overrides[get_db] = get_test_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def login(client, email, password=PASSWORD):
    return client.post("/login", data={"email": email, "password": password},
                       follow_redirects=False)


# --- Logging in -------------------------------------------------------------
def test_login_page_loads(client):
    assert client.get("/login").status_code == 200


def test_correct_login_sets_cookie_and_redirects_by_role(client):
    r = login(client, "manager@test.com")
    assert r.status_code == 303
    assert r.headers["location"] == "/manager"
    assert COOKIE_NAME in r.cookies

    r = login(client, "tenant@test.com")
    assert r.headers["location"] == "/home"


def test_email_is_not_case_sensitive(client):
    assert login(client, "  Manager@Test.com ").status_code == 303


def test_wrong_password_is_rejected(client):
    r = login(client, "manager@test.com", "wrong")
    assert r.status_code == 401
    assert COOKIE_NAME not in r.cookies


def test_unknown_email_gives_same_message_as_wrong_password(client):
    wrong_pw = login(client, "manager@test.com", "wrong")
    no_user = login(client, "nobody@test.com", "wrong")
    assert no_user.status_code == wrong_pw.status_code == 401
    assert "Wrong email or password" in no_user.text
    assert "Wrong email or password" in wrong_pw.text


# --- The session cookie -----------------------------------------------------
def test_cookie_is_httponly(client):
    set_cookie = login(client, "manager@test.com").headers["set-cookie"].lower()
    assert "httponly" in set_cookie
    assert "samesite=lax" in set_cookie


def test_me_shows_logged_in_user(client):
    login(client, "manager@test.com")
    r = client.get("/me")
    assert r.status_code == 200
    assert r.json()["role"] == "manager"


def test_no_cookie_means_not_logged_in(client):
    assert client.get("/me").status_code == 401


def test_browser_without_cookie_is_sent_to_login(client):
    r = client.get("/me", headers={"accept": "text/html"}, follow_redirects=False)
    assert r.headers["location"] == "/login"


def test_tampered_cookie_is_rejected(client):
    """A tenant edits their token to say "manager". The signature no longer matches."""
    login(client, "tenant@test.com")
    header, payload, signature = client.cookies[COOKIE_NAME].split(".")

    # The middle part is just base64 JSON: anyone can read and change it...
    data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    data["role"] = "manager"
    data["sub"] = "2"  # and pretend to be the manager's user id
    forged = base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()

    # ...but without SECRET_KEY they can't make a matching signature.
    client.cookies.clear()  # replace the real cookie, don't add a second one
    client.cookies.set(COOKIE_NAME, f"{header}.{forged}.{signature}")
    assert client.get("/me").status_code == 401
    assert client.get("/test-manager-only").status_code == 401


def test_logout_ends_the_session(client):
    login(client, "manager@test.com")
    r = client.post("/logout", follow_redirects=False)
    assert r.headers["location"] == "/login"
    assert client.get("/me").status_code == 401


# --- Roles ------------------------------------------------------------------
def test_manager_can_open_manager_page(client):
    login(client, "manager@test.com")
    assert client.get("/test-manager-only").status_code == 200


def test_tenant_cannot_open_manager_page(client):
    login(client, "tenant@test.com")
    assert client.get("/test-manager-only").status_code == 403


# --- Passwords --------------------------------------------------------------
def test_password_is_never_stored_in_plain_text():
    hashed = hash_password(PASSWORD)
    assert PASSWORD not in hashed
    assert hashed.startswith("$argon2")
