import json, os
import paho.mqtt.publish as publish
from dotenv import load_dotenv

load_dotenv()
publish.single(
    "bv/rooms/1/readings",
    json.dumps({"co2": 820, "temp": 21.5, "humidity": 45}),
    hostname=os.getenv("MQTT_HOST"),
    port=int(os.getenv("MQTT_PORT", 8883)),
    auth={"username": os.getenv("MQTT_USER"), "password": os.getenv("MQTT_PASS")},
    tls={},
)
print("Sent")