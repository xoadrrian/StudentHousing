"""
database.py - one place that knows how to talk to the database.

Every other file imports `Base` (to define tables) and `get_db` (to get a
session inside a route). Nobody else should create their own engine.
"""
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# Reads the .env file in the project folder into environment variables.
load_dotenv()

# Supabase link from the team (.env). If it's missing we fall back to a local
# SQLite file, so you can work and test without internet or the password.
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./local.db")

# SQLite needs this one extra setting to work with FastAPI; Postgres doesn't.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# pool_pre_ping: test a connection before using it, so a connection Supabase
# closed in the background doesn't crash a request.
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)

# A "session" is one conversation with the database (a few queries + commit).
SessionLocal = sessionmaker(bind=engine, autoflush=False)


class Base(DeclarativeBase):
    """Parent class for every table in models.py."""


def get_db():
    """FastAPI dependency: opens a session for one request and always closes it."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
