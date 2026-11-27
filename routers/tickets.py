from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, Form, File, UploadFile
from sqlalchemy.orm import Session

from database import get_db
from models import Role, User, Ticket, TicketPhoto
from routers.auth import require_role

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.post("/submit")
def submit_ticket(
    title: str = Form(...),
    description: str = Form(...),
    image: UploadFile | None = File(None),
    user: User = Depends(require_role(Role.tenant)),
    db: Session = Depends(get_db),
):
    ticket = Ticket(
        tenant_id=user.id,
        worker_id=None,
        title=title,
        description=description,
        status="open",
        created_at=datetime.utcnow(),
    )

    db.add(ticket)
    db.commit()
    db.refresh(ticket)

    print("Image object:", image)

    if image and image.filename:

        print("Image filename:", image.filename)
        
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)

        file_path = upload_dir / f"{ticket.id}_{image.filename}"

        with open(file_path, "wb") as buffer:
            buffer.write(image.file.read())

        photo = TicketPhoto(
            ticket_id=ticket.id,
            storage_path=str(file_path),
            uploaded_at=datetime.utcnow(),
        )

        db.add(photo)
        db.commit()

    return {
        "message": "Ticket submitted successfully",
        "ticket_id": ticket.id,
        "tenant_id": str(ticket.tenant_id),
        "title": ticket.title,
        "description": ticket.description,
        "status": ticket.status,
    }