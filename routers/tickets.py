<<<<<<< Updated upstream
=======
from fastapi import APIRouter, Form
from uuid import UUID

router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)

@router.post("/submit")
def submit_ticket(
    tenant_id: UUID = Form(...),
    title: str = Form(...),
    description: str = Form(...)
):
    return {
        "message": "Ticket submitted successfully",
        "ticket": {
            "tenant_id": str(tenant_id),
            "title": title,
            "description": description,
            "status": "Open"
        }
    }
>>>>>>> Stashed changes
