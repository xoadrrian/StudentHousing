from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import Role, SensorReading, User
from routers.auth import require_role

router = APIRouter(prefix="/api/sensors", tags=["sensors"])

def reading_to_dict(reading: SensorReading) -> dict:
    return {
        "room_id": reading.room_id,
        "measured_at": reading.measured_at,
        "co2_ppm": reading.co2_ppm,
        "temperature_c": reading.temperature_c,
        "humidity_pct": reading.humidity_pct,
    }


@router.get("/rooms/{room_id}/latest")
def get_latest_reading(room_id: int, db: Session = Depends(get_db)):
    query = (
    select(SensorReading)
    .where(SensorReading.room_id == room_id)
    .order_by(SensorReading.measured_at.desc())
    .limit(1)
    )
    reading = db.scalars(query).first()

    if reading is None:
        raise HTTPException(status_code=404, detail="No readings for this room")

    return reading_to_dict(reading)


@router.get("/rooms/{room_id}/history")
def get_reading_history(
    room_id: int,
    hours: int = Query(default=24, ge=1, le=168),
    db: Session = Depends(get_db),
):
    since = datetime.now(timezone.utc) - timedelta(hours=hours)

    query = (
        select(SensorReading)
        .where(SensorReading.room_id == room_id)
        .where(SensorReading.measured_at >= since)
        .order_by(SensorReading.measured_at.asc())
    )
    readings = db.scalars(query).all()

    return [reading_to_dict(r) for r in readings]

@router.get("/my-room/latest")
def get_my_room_latest(
    user: User = Depends(require_role(Role.tenant)),
    db: Session = Depends(get_db),
):
    return get_latest_reading(user.tenant.room_id, db)