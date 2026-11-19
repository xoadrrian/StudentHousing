# routers/pages.py
from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates

from models import Role, User
from routers.auth import require_role

router = APIRouter()
templates = Jinja2Templates(directory="templates")


@router.get("/home")
def home(request: Request, user: User = Depends(require_role(Role.tenant))):
    return templates.TemplateResponse(request, "home.html", {"user": user})


@router.get("/manager")
def manager_home(request: Request, user: User = Depends(require_role(Role.manager))):
    return templates.TemplateResponse(request, "manager.html", {"user": user})