from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class TicketCreate(BaseModel):
    title: str
    description: str


class TicketResponse(BaseModel):
    id: int
    tenant_id: UUID
    worker_id: Optional[UUID] = None
    title: str
    description: str
    status: str
    created_at: datetime