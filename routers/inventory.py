import uuid

from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import Role, Room, SupplyItem, SupplyItemMember, Tenant, User
from routers.auth import require_role

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])
tenant_only = require_role(Role.tenant)


# ---------- helpers ----------

def my_building_id(user: User, db: Session) -> int:
    room = db.get(Room, user.tenant.room_id)
    return room.building_id


def get_my_item(item_id: int, user: User, db: Session) -> SupplyItem:
    item = db.get(SupplyItem, item_id)
    if item is None or item.building_id != my_building_id(user, db):
        raise HTTPException(404, "Item not found")
    return item


def next_person(item: SupplyItem) -> uuid.UUID | None:
    turns = [m.tenant_id for m in item.members]
    if len(turns) < 2 or item.responsible_id not in turns:
        return None
    now = turns.index(item.responsible_id)
    return turns[(now + 1) % len(turns)]


def first_name(user_id: uuid.UUID | None, db: Session) -> str | None:
    if user_id is None:
        return None
    person = db.get(User, user_id)
    return person.first_name if person else None


def item_to_dict(item: SupplyItem, user: User, db: Session) -> dict:
    return {
        "id": item.id,
        "name": item.name,
        "status": item.status,
        "responsible_id": str(item.responsible_id) if item.responsible_id else None,
        "responsible_name": first_name(item.responsible_id, db),
        "next_name": first_name(next_person(item), db),
        "is_mine": item.responsible_id == user.id,
    }


# ---------- reading ----------

@router.get("")
def list_items(user: User = Depends(tenant_only), db: Session = Depends(get_db)):
    building_id = my_building_id(user, db)
    items = db.scalars(
        select(SupplyItem)
        .where(SupplyItem.building_id == building_id)
        .order_by(SupplyItem.name)
    ).all()
    return [item_to_dict(i, user, db) for i in items]


@router.get("/tenants")
def list_housemates(user: User = Depends(tenant_only), db: Session = Depends(get_db)):
    building_id = my_building_id(user, db)
    room_ids = db.scalars(select(Room.id).where(Room.building_id == building_id)).all()
    tenants = db.scalars(select(Tenant).where(Tenant.room_id.in_(room_ids))).all()
    return [{"id": str(t.user_id), "name": t.user.first_name} for t in tenants]


# ---------- changing ----------

@router.post("")
def add_item(
    title: str = Form(...),
    member_ids: list[uuid.UUID] = Form(default=[]),
    user: User = Depends(tenant_only),
    db: Session = Depends(get_db),
):
    name = title.strip()
    if not name:
        raise HTTPException(400, "Name is required")

    building_id = my_building_id(user, db)

    people = list(dict.fromkeys(member_ids))  # remove doubles, keep the order
    for person_id in people:
        tenant = db.get(Tenant, person_id)
        if tenant is None or db.get(Room, tenant.room_id).building_id != building_id:
            raise HTTPException(400, "Someone you picked doesn't live in your house")

    item = SupplyItem(
        building_id=building_id,
        name=name,
        quantity=1,
        responsible_id=people[-1] if people else None,
        status="in_stock",
    )
    item.members = [
        SupplyItemMember(tenant_id=person_id, position=place)
        for place, person_id in enumerate(people)
    ]
    db.add(item)
    db.commit()
    return item_to_dict(item, user, db)


@router.post("/{item_id}/to-buy")
def mark_to_buy(item_id: int, user: User = Depends(tenant_only), db: Session = Depends(get_db)):
    item = get_my_item(item_id, user, db)
    if item.status == "in_stock":
        item.status = "to_buy"
        upcoming = next_person(item)
        if upcoming is not None:
            item.responsible_id = upcoming
        db.commit()
    return item_to_dict(item, user, db)


@router.post("/{item_id}/bought")
def mark_bought(item_id: int, user: User = Depends(tenant_only), db: Session = Depends(get_db)):
    item = get_my_item(item_id, user, db)
    if item.status == "to_buy":
        item.status = "in_stock"
        db.commit()
    return item_to_dict(item, user, db)


@router.delete("/{item_id}")
def delete_item(item_id: int, user: User = Depends(tenant_only), db: Session = Depends(get_db)):
    item = get_my_item(item_id, user, db)
    db.delete(item)
    db.commit()
    return {"deleted": item_id}