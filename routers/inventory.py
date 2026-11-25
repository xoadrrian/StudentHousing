import uuid

from fastapi import APIRouter, Depends, Form, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import get_db
from models import Role, Room, SupplyItem, Tenant, User
from routers.auth import require_role

router = APIRouter(prefix="/api/inventory", tags=["Inventory"])
tenant_only = require_role(Role.tenant)


def my_building_id(user: User, db: Session) -> int:
    room = db.get(Room, user.tenant.room_id)
    return room.building_id


def get_my_item(item_id: int, user: User, db: Session) -> SupplyItem:
    item = db.get(SupplyItem, item_id)
    if item is None or item.building_id != my_building_id(user, db):
        raise HTTPException(404, "Item not found")
    return item


def item_to_dict(item: SupplyItem, user: User, db: Session) -> dict:
    responsible = db.get(User, item.responsible_id) if item.responsible_id else None
    return {
        "id": item.id,
        "name": item.name,
        "status": item.status,
        "responsible_id": str(item.responsible_id) if item.responsible_id else None,
        "responsible_name": responsible.first_name if responsible else None,
        "is_mine": item.responsible_id == user.id,
    }



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



@router.post("")
def add_item(
    title: str = Form(...),
    responsible_id: uuid.UUID | None = Form(None),
    user: User = Depends(tenant_only),
    db: Session = Depends(get_db),
):
    name = title.strip()
    if not name:
        raise HTTPException(400, "Name is required")

    building_id = my_building_id(user, db)

    if responsible_id is not None:
        tenant = db.get(Tenant, responsible_id)
        if tenant is None or db.get(Room, tenant.room_id).building_id != building_id:
            raise HTTPException(400, "That person doesn't live in your house")

    item = SupplyItem(
        building_id=building_id,
        name=name,
        quantity=1,
        responsible_id=responsible_id,
        status="in_stock",
    )
    db.add(item)
    db.commit()
    return item_to_dict(item, user, db)


@router.post("/{item_id}/to-buy")
def mark_to_buy(item_id: int, user: User = Depends(tenant_only), db: Session = Depends(get_db)):
    item = get_my_item(item_id, user, db)
    item.status = "to_buy"
    db.commit()
    return item_to_dict(item, user, db)


@router.post("/{item_id}/bought")
def mark_bought(item_id: int, user: User = Depends(tenant_only), db: Session = Depends(get_db)):
    item = get_my_item(item_id, user, db)
    item.status = "in_stock"
    db.commit()
    return item_to_dict(item, user, db)


@router.delete("/{item_id}")
def delete_item(item_id: int, user: User = Depends(tenant_only), db: Session = Depends(get_db)):
    item = get_my_item(item_id, user, db)
    db.delete(item)
    db.commit()
    return {"deleted": item_id}