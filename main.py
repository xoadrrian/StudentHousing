from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi import Request
from fastapi.templating import Jinja2Templates
from routers import sensors

import mqtt_listener

@asynccontextmanager
async def lifespan(app):
    client = mqtt_listener.start()   # when the app starts
    yield
    client.loop_stop()               # when the app stops
    client.disconnect()


app = FastAPI(lifespan=lifespan)
app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(sensors.router)

templates = Jinja2Templates(directory="templates")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/home")
def home_page(request: Request):
    return templates.TemplateResponse(request, "home.html")

@app.get("/myTickets")
def myTickets_page(request: Request):
    return templates.TemplateResponse(request, "myTickets.html")

@app.get("/")
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html")

@app.get("/addItem")
def addItem_page(request: Request):
    return templates.TemplateResponse(request, "addItem.html")

@app.get("/communityComplaint")
def communityComplaint_page(request: Request):
    return templates.TemplateResponse(request, "communityComplaint.html")

@app.get("/repairTicket")
def repairTicket_page(request: Request):
    return templates.TemplateResponse(request, "repairTicket.html")