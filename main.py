from contextlib import asynccontextmanager
import logging
import os

from fastapi import FastAPI

import models
import mqtt_listener
from database import Base, engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app):
    Base.metadata.create_all(bind=engine)
    client = None
    if os.getenv("MQTT_HOST"):
        client = mqtt_listener.start()
    else:
        logger.info("MQTT_HOST is not set; MQTT listener is disabled.")

    try:
        yield
    finally:
        if client is not None:
            client.loop_stop()
            client.disconnect()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}

from routers import tickets

app.include_router(tickets.router)