import json
import os
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
from dotenv import load_dotenv

from database import SessionLocal
from models import SensorReading

load_dotenv()

TOPIC = "bv/rooms/+/readings"  # + = any room id

connected = False  # updated by on_connect / on_disconnect, read by /health/mqtt


def is_connected():
    return connected


def on_connect(client, userdata, flags, reason_code, properties):
    global connected
    if reason_code.is_failure:
        print("MQTT connect failed:", reason_code)
        connected = False
        return
    print("Connected to MQTT")
    connected = True
    client.subscribe(TOPIC, qos=1)


def on_disconnect(client, userdata, flags, reason_code, properties):
    global connected
    connected = False
    print("MQTT disconnected:", reason_code)


def on_message(client, userdata, msg):
    # topic looks like: bv/rooms/3/readings
    try:
        room_id = int(msg.topic.split("/")[2])
        data = json.loads(msg.payload)
    except (ValueError, IndexError):
        print("Bad message on", msg.topic)
        return

    with SessionLocal() as db:
        db.add(SensorReading(
            room_id=room_id,
            measured_at=datetime.now(timezone.utc),
            co2_ppm=data.get("co2"),
            temperature_c=data.get("temp"),
            humidity_pct=data.get("humidity"),
        ))
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            print("DB error:", e)
            return

    print("Saved room", room_id, data)


def start():
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(os.getenv("MQTT_USER"), os.getenv("MQTT_PASS"))
    client.tls_set()  # port 8883 is encrypted
    client.on_connect = on_connect
    client.on_disconnect = on_disconnect
    client.on_message = on_message
    client.connect_async(os.getenv("MQTT_HOST"), int(os.getenv("MQTT_PORT", 8883)))
    client.loop_start()  # runs in the background
    return client