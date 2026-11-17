from contextlib import asynccontextmanager
from fastapi import FastAPI

import mqtt_listener


@asynccontextmanager
async def lifespan(app):
    client = mqtt_listener.start()   # when the app starts
    yield
    client.loop_stop()               # when the app stops
    client.disconnect()


app = FastAPI(lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok"}