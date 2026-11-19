<<<<<<< Updated upstream
=======
from fastapi import APIRouter
from models import TicketCreate

router = APIRouter(
    prefix="/tickets",
    tags=["Tickets"]
)

@router.post("/submit")
def submit_ticket(ticket: TicketCreate):

    ticket_data = {
        "tenant_id": str(ticket.tenant_id),
        "worker_id": None,
        "title": ticket.title,
        "description": ticket.description,
        "status": "Open"
    }


    return {
        "message": "Ticket submitted successfully",
        "ticket": ticket_data
    }
>>>>>>> Stashed changes
