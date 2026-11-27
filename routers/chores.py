import uuid
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import Chore, ChoreAssignment, ChoreMember, Role, Room, Tenant, User
from routers.auth import require_role
from routers.inventory import my_building_id

router = APIRouter(prefix="/api/chores", tags=["Chores"])
tenant_only = require_role(Role.tenant)

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]


# ---------- helpers ----------

def chore_days(chore: Chore) -> list[int]:
    """The weekdays of a chore as numbers: Monday = 0 ... Sunday = 6."""
    days = [int(d) for d in chore.weekdays.split(",") if d != ""]
    return days or list(range(7))  # nothing saved = every day


def next_due(chore: Chore, from_day: date) -> date:
    """The first day on or after `from_day` that is one of the chore's weekdays."""
    days = chore_days(chore)
    day = from_day
    while day.weekday() not in days:
        day += timedelta(days=1)
    return day


def repeat_text(chore: Chore) -> str:
    days = chore_days(chore)
    if len(days) == 7:
        return "Every day"
    if days == [0, 1, 2, 3, 4]:
        return "Every weekday"
    names = [DAY_NAMES[d] for d in days]
    if len(names) == 1:
        return "Every " + names[0]
    return "Every " + ", ".join(names[:-1]) + " and " + names[-1]


def get_my_chore(chore_id: int, user: User, db: Session) -> Chore:
    chore = db.get(Chore, chore_id)
    if chore is None or chore.building_id != my_building_id(user, db):
        raise HTTPException(404, "Chore not found")
    return chore


def open_turn(chore: Chore) -> ChoreAssignment | None:
    for turn in chore.turns:
        if turn.completed_at is None:
            return turn
    return None


def person_after(chore: Chore, person_id: uuid.UUID) -> uuid.UUID:
    wheel = [m.tenant_id for m in chore.members]
    if person_id not in wheel:
        return wheel[0] if wheel else person_id
    now = wheel.index(person_id)
    return wheel[(now + 1) % len(wheel)]


def first_name(user_id: uuid.UUID, db: Session) -> str:
    person = db.get(User, user_id)
    return person.first_name if person else "?"


# ---------- reading ----------

@router.get("/week")
def week_schedule(start: date, user: User = Depends(tenant_only), db: Session = Depends(get_db)):
    """Everything that happens in the 7 days from `start`: done turns,
    the open turn, and the turns that are expected to come after it."""
    end = start + timedelta(days=6)
    today = date.today()
    chores = db.scalars(select(Chore).where(Chore.building_id == my_building_id(user, db))).all()

    items = []
    for chore in chores:
        # turns that were already done this week
        for turn in chore.turns:
            if turn.completed_at is not None and start <= turn.due_date <= end:
                items.append((turn.due_date, chore, turn.tenant_id, "done"))

        turn = open_turn(chore)
        if turn is None:
            continue

        # the open turn: if it is late, show it on today as overdue
        if turn.due_date < today:
            if start <= today <= end:
                items.append((today, chore, turn.tenant_id, "overdue"))
        elif turn.due_date <= end:
            items.append((turn.due_date, chore, turn.tenant_id, "open"))

        # the turns after it (predicted from the weekdays and the wheel)
        when, who = turn.due_date, turn.tenant_id
        while True:
            when = next_due(chore, when + timedelta(days=1))
            who = person_after(chore, who)
            if when > end:
                break
            if when >= start and when >= today:
                items.append((when, chore, who, "upcoming"))

    result = []
    for when, chore, person, state in sorted(items, key=lambda i: (i[0], i[1].title)):
        upcoming = person_after(chore, person)
        result.append({
            "date": when.isoformat(),
            "chore_id": chore.id,
            "title": chore.title,
            "repeats": repeat_text(chore),
            "person_name": first_name(person, db),
            "is_mine": person == user.id,
            "next_name": first_name(upcoming, db) if upcoming != person else None,
            "members": [first_name(m.tenant_id, db) for m in chore.members],
            "state": state,
        })
    return result


@router.get("/todo")
def my_todo(user: User = Depends(tenant_only), db: Session = Depends(get_db)):
    turns = db.scalars(
        select(ChoreAssignment)
        .where(ChoreAssignment.tenant_id == user.id, ChoreAssignment.completed_at.is_(None))
        .order_by(ChoreAssignment.due_date)
    ).all()
    return [
        {
            "turn_id": t.id,
            "title": db.get(Chore, t.chore_id).title,
            "due_date": t.due_date.isoformat(),
            "overdue": t.due_date < date.today(),
        }
        for t in turns
    ]


# ---------- changing ----------

@router.post("")
def add_chore(
    title: str = Form(...),
    weekdays: list[int] = Form(default=[]),
    member_ids: list[uuid.UUID] = Form(default=[]),
    user: User = Depends(tenant_only),
    db: Session = Depends(get_db),
):
    name = title.strip()
    if not name:
        raise HTTPException(400, "Title is required")

    days = sorted(set(weekdays))
    if not days or any(d < 0 or d > 6 for d in days):
        raise HTTPException(400, "Pick at least one day")

    people = list(dict.fromkeys(member_ids))  # remove doubles, keep the order
    if not people:
        raise HTTPException(400, "Pick at least one person")

    building_id = my_building_id(user, db)
    for person_id in people:
        tenant = db.get(Tenant, person_id)
        if tenant is None or db.get(Room, tenant.room_id).building_id != building_id:
            raise HTTPException(400, "Someone you picked doesn't live in your house")

    chore = Chore(building_id=building_id, title=name, weekdays=",".join(str(d) for d in days))
    chore.members = [ChoreMember(tenant_id=p, position=i) for i, p in enumerate(people)]
    chore.turns = [ChoreAssignment(tenant_id=people[0], due_date=next_due(chore, date.today()))]
    db.add(chore)
    db.commit()
    return {"id": chore.id}


@router.post("/turns/{turn_id}/done")
def mark_done(turn_id: int, user: User = Depends(tenant_only), db: Session = Depends(get_db)):
    turn = db.get(ChoreAssignment, turn_id)
    if turn is None:
        raise HTTPException(404, "Turn not found")
    chore = get_my_chore(turn.chore_id, user, db)

    if turn.completed_at is None:
        turn.completed_at = datetime.now(timezone.utc)
        chore.turns.append(ChoreAssignment(
            tenant_id=person_after(chore, turn.tenant_id),
            due_date=next_due(chore, turn.due_date + timedelta(days=1)),
        ))
        db.commit()
    return {"done": turn_id}


@router.delete("/{chore_id}")
def delete_chore(chore_id: int, user: User = Depends(tenant_only), db: Session = Depends(get_db)):
    chore = get_my_chore(chore_id, user, db)
    db.delete(chore)
    db.commit()
    return {"deleted": chore_id}