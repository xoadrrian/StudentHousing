"""
models.py - the database tables, written as Python classes (from the ERD).

Teammates add their own tables (Property, Ticket, Chore...) below in the same style.
"""
import enum
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, Enum, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Role(str, enum.Enum):
    """The three roles from the ERD. Decides which pages a user may open."""
    tenant = "tenant"
    manager = "manager"
    worker = "worker"


class User(Base):
    __tablename__ = "users"  # "user" is a reserved word in Postgres, so plural

    user_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    surname: Mapped[str] = mapped_column(String(100))
    # unique + index: no two accounts with one email, and fast lookup at login
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # Never the real password: only the Argon2 hash (see routers/auth.py, step 2)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role, name="user_role"))


class SensorReading(Base):
    """One reading from a room device, saved by mqtt_listener.py."""
    __tablename__ = "sensor_reading"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    room_id: Mapped[int]
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    co2_ppm: Mapped[int | None]
    temperature_c: Mapped[Decimal | None] = mapped_column(Numeric)
    humidity_pct: Mapped[Decimal | None] = mapped_column(Numeric)
