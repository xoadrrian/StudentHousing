from datetime import datetime
from decimal import Decimal
from sqlalchemy import BigInteger, DateTime, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class SensorReading(Base):
    __tablename__ = "sensor_reading"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    room_id: Mapped[int]
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    co2_ppm: Mapped[int | None]
    temperature_c: Mapped[Decimal | None] = mapped_column(Numeric)
    humidity_pct: Mapped[Decimal | None] = mapped_column(Numeric)


from pydantic import BaseModel
from uuid import UUID
from typing import Optional
from datetime import datetime

class TicketCreate(BaseModel):
    tenant_id: UUID
    title: str
    description: str

class TicketResponse(BaseModel):
    id: int
    tenant_id: UUID
    worker_id: Optional[UUID] = None
    title: str
    description: str
    status: str
    created_at: datetime