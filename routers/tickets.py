from fastapi import APIRouter, Depends, Form

from models import Role, User
from routers.auth import require_role

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.post("/submit")
def submit_ticket(
    title: str = Form(...),
    description: str = Form(...),
    user: User = Depends(require_role(Role.tenant)),
):
    return {
        "message": "Ticket submitted successfully",
        "ticket": {
            "tenant_id": str(user.id),
            "title": title,
            "description": description,
            "status": "Open",
        },
    }