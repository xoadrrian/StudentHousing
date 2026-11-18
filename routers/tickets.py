from fastapi import APIRouter
from uuid import UUID
from datetime import datetime

router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)

tickets = []

@router.post("/submit")
def submit_ticket(
    tenant_id: UUID,
    title: str,
    description: str
):
    ticket = {
        "tenant_id": str(tenant_id),
        "worker_id": None,
        "title": title,
        "description": description,
        "status": "Open"
    }

    result = supabase.table("ticket").insert(ticket).execute()

    return {
        "message": "Ticket submitted successfully",
        "data": result.data
    }