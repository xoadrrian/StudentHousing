from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

from models import Role, User
from routers.auth import require_role

router = APIRouter()
templates = Jinja2Templates(directory="templates")

tenant_only = require_role(Role.tenant)


@router.get("/home")
def home(request: Request, user: User = Depends(tenant_only)):
    return templates.TemplateResponse(request, "home.html", {"user": user})


@router.get("/myTickets")
def my_tickets(request: Request, user: User = Depends(tenant_only)):
    return templates.TemplateResponse(request, "myTickets.html", {"user": user})


@router.get("/addItem")
def add_item(request: Request, user: User = Depends(tenant_only)):
    return templates.TemplateResponse(request, "addItem.html", {"user": user})


@router.get("/addChore")
def add_chore(request: Request, user: User = Depends(tenant_only)):
    return templates.TemplateResponse(request, "addChore.html", {"user": user})


@router.get("/ticketDetails")
def ticket_details(request: Request, user: User = Depends(require_role(Role.tenant, Role.worker))):
    return templates.TemplateResponse(request, "ticketDetails.html", {"user": user})


@router.get("/communityComplaint")
def community_complaint(request: Request, user: User = Depends(tenant_only)):
    return templates.TemplateResponse(request, "communityComplaint.html", {"user": user})


@router.get("/repairTicket")
def repair_ticket(request: Request, user: User = Depends(tenant_only)):
    return templates.TemplateResponse(request, "repairTicket.html", {"user": user})


@router.get("/manager")
def manager_home(request: Request, user: User = Depends(require_role(Role.manager))):
    return templates.TemplateResponse(request, "manager.html", {"user": user})


@router.get("/worker")
def worker_home(request: Request, user: User = Depends(require_role(Role.worker))):
    return templates.TemplateResponse(request, "worker.html", {"user": user})
