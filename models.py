from datetime import datetime
from decimal import Decimal
from sqlalchemy import DateTime, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column
from database import Base


class SensorReading(Base):
    __tablename__ = "sensor_reading"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    room_id: Mapped[int]
    measured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    co2_ppm: Mapped[int | None]
    temperature_c: Mapped[Decimal | None] = mapped_column(Numeric)
    humidity_pct: Mapped[Decimal | None] = mapped_column(Numeric)