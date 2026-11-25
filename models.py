import enum
import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, ForeignKey, Integer, Numeric, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database import Base


class Role(str, enum.Enum):
    tenant = "tenant"
    manager = "manager"
    worker = "worker"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True)
    first_name: Mapped[str] = mapped_column(Text)
    last_name: Mapped[str] = mapped_column(Text)
    email: Mapped[str] = mapped_column(Text, unique=True)

    tenant: Mapped["Tenant | None"] = relationship(back_populates="user", lazy="selectin")
    manager: Mapped["Manager | None"] = relationship(back_populates="user", lazy="selectin")
    worker: Mapped["Worker | None"] = relationship(back_populates="user", lazy="selectin")

    @property
    def role(self) -> Role | None:
        if self.manager is not None:
            return Role.manager
        if self.worker is not None:
            return Role.worker
        if self.tenant is not None:
            return Role.tenant
        return None


class Tenant(Base):
    __tablename__ = "tenant"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)

    room_id: Mapped[int] = mapped_column(Integer)

    user: Mapped[User] = relationship(back_populates="tenant")


class Manager(Base):
    __tablename__ = "manager"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)

    user: Mapped[User] = relationship(back_populates="manager")


class Worker(Base):
    __tablename__ = "worker"

    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"), primary_key=True)

    user: Mapped[User] = relationship(back_populates="worker")


class SensorReading(Base):
    __tablename__ = "sensor_reading"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    room_id: Mapped[int]
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    co2_ppm: Mapped[int | None]
    temperature_c: Mapped[Decimal | None] = mapped_column(Numeric)
    humidity_pct: Mapped[Decimal | None] = mapped_column(Numeric)

class Ticket(Base):
    __tablename__ = "ticket"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid)
    worker_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    title: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

class Room(Base):
    __tablename__ = "room"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    building_id: Mapped[int] = mapped_column(Integer)
    number: Mapped[str] = mapped_column(Text)

class SupplyItem(Base):
    __tablename__ = "supply_item"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    building_id: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(Text)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    responsible_id: Mapped[uuid.UUID | None] = mapped_column(Uuid)
    status: Mapped[str] = mapped_column(Text, default="in_stock")