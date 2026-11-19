import base64
import json
import uuid

import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import routers.auth as auth
from database import get_db
from main import app
from models import Base, Manager, Role, Tenant, User, Worker
from routers.auth import COOKIE_NAME, require_role

PASSWORD = "Test1234!"
TENANT_ID = uuid.uuid4()
MANAGER_ID = uuid.uuid4()
WORKER_ID = uuid.uuid4()
NO_ROLE_ID = uuid.uuid4()

FAKE_ACCOUNTS = {
    "tenant@test.com": TENANT_ID,
    "manager@test.com": MANAGER_ID,
    "worker@test.com": WORKER_ID,
    "norole@test.com": NO_ROLE_ID,
}


def fake_supabase_sign_in(email, password):
    if email in FAKE_ACCOUNTS and password == PASSWORD:
        return FAKE_ACCOUNTS[email]
    return None


@app.get("/test-manager-only")
def manager_only(user: User = Depends(require_role(Role.manager))):
    return {"ok": True}


@pytest.fixture
def client(monkeypatch):
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    Base.metadata.create_all(engine)
    TestSession = sessionmaker(bind=engine)

    with TestSession() as db:
        db.add_all([
            User(id=TENANT_ID, first_name="Emma", last_name="Johnson", email="tenant@test.com"),
            User(id=MANAGER_ID, first_name="John", last_name="Doe", email="manager@test.com"),
            User(id=WORKER_ID, first_name="Alice", last_name="Smith", email="worker@test.com"),
            User(id=NO_ROLE_ID, first_name="New", last_name="Person", email="norole@test.com"),
            Tenant(user_id=TENANT_ID, room_id=1),
            Manager(user_id=MANAGER_ID),
            Worker(user_id=WORKER_ID),
        ])
        db.commit()

    def get_test_db():
        db = TestSession()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = get_test_db
    monkeypatch.setattr(auth, "supabase_sign_in", fake_supabase_sign_in)
    yield TestClient(app)
    app.dependency_overrides.clear()


def login(client, email, password=PASSWORD):
    return client.post("/login", data={"email": email, "password": password},
                       follow_redirects=False)


def test_login_page_loads(client):
    assert client.get("/login").status_code == 200


def test_correct_login_sets_cookie_and_redirects_by_role(client):
    r = login(client, "manager@test.com")
    assert r.status_code == 303
    assert r.headers["location"] == "/manager"
    assert COOKIE_NAME in r.cookies

    assert login(client, "tenant@test.com").headers["location"] == "/home"
    assert login(client, "worker@test.com").headers["location"] == "/worker"


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


def test_account_without_a_role_cannot_log_in(client):
    r = login(client, "norole@test.com")
    assert r.status_code == 403
    assert COOKIE_NAME not in r.cookies


def test_supabase_down_shows_a_clear_error(client, monkeypatch):
    def down(email, password):
        raise auth.LoginServiceDown("no internet")
    monkeypatch.setattr(auth, "supabase_sign_in", down)
    r = login(client, "manager@test.com")
    assert r.status_code == 503
    assert COOKIE_NAME not in r.cookies


def test_cookie_is_httponly(client):
    set_cookie = login(client, "manager@test.com").headers["set-cookie"].lower()
    assert "httponly" in set_cookie
    assert "samesite=lax" in set_cookie


def test_me_shows_logged_in_user(client):
    login(client, "manager@test.com")
    r = client.get("/me")
    assert r.status_code == 200
    assert r.json()["role"] == "manager"
    assert r.json()["id"] == str(MANAGER_ID)


def test_no_cookie_means_not_logged_in(client):
    assert client.get("/me").status_code == 401


def test_browser_without_cookie_is_sent_to_login(client):
    r = client.get("/me", headers={"accept": "text/html"}, follow_redirects=False)
    assert r.headers["location"] == "/login"


def test_tampered_cookie_is_rejected(client):
    login(client, "tenant@test.com")
    header, payload, signature = client.cookies[COOKIE_NAME].split(".")

    data = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    data["role"] = "manager"
    data["sub"] = str(MANAGER_ID)
    forged = base64.urlsafe_b64encode(json.dumps(data).encode()).rstrip(b"=").decode()

    client.cookies.clear()
    client.cookies.set(COOKIE_NAME, f"{header}.{forged}.{signature}")
    assert client.get("/me").status_code == 401
    assert client.get("/test-manager-only").status_code == 401


def test_logout_ends_the_session(client):
    login(client, "manager@test.com")
    r = client.post("/logout", follow_redirects=False)
    assert r.headers["location"] == "/login"
    assert client.get("/me").status_code == 401


def test_manager_can_open_manager_page(client):
    login(client, "manager@test.com")
    assert client.get("/test-manager-only").status_code == 200


def test_tenant_cannot_open_manager_page(client):
    login(client, "tenant@test.com")
    assert client.get("/test-manager-only").status_code == 403


def test_no_password_is_stored_in_our_tables():
    columns = {c.name for c in User.__table__.columns}
    assert not any("pass" in c for c in columns)
