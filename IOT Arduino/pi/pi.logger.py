import json, sqlite3, threading, time
import paho.mqtt.client as mqtt
from flask import Flask, jsonify, request

# Fill these in on the Pi only. Never commit real values.
CLOUD_HOST = "YOUR_EMQX_HOST"
CLOUD_USER = "YOUR_USERNAME"
CLOUD_PASS = "YOUR_PASSWORD"
CLOUD_TOPIC = "bv/rooms/1/readings"

db = sqlite3.connect("/home/miraik/readings.db", check_same_thread=False)
db.execute("CREATE TABLE IF NOT EXISTS readings (ts INTEGER, room TEXT, data TEXT)")
lock = threading.Lock()
last_cloud = 0

def new_client():
    try:
        return mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    except AttributeError:
        return mqtt.Client()

# Cloud broker (EMQX)
cloud = new_client()
cloud.username_pw_set(CLOUD_USER, CLOUD_PASS)
cloud.tls_set()
cloud.on_connect = lambda c, *a: print("Connected to EMQX")
cloud.connect_async(CLOUD_HOST, 8883)
cloud.loop_start()

def on_connect(c, *a):
    c.subscribe("house/+/+/climate")

def on_message(c, u, m):
    global last_cloud
    try:
        data = m.payload.decode(); d = json.loads(data)
    except Exception:
        return
    room = "/".join(m.topic.split("/")[1:3])
    with lock:
        db.execute("INSERT INTO readings VALUES (?,?,?)", (int(time.time()), room, data))
        db.commit()
    if time.time() - last_cloud >= 30:
        last_cloud = time.time()
        msg = json.dumps({"co2": d["co2"], "temp": d["temp"], "humidity": d["hum"]})
        cloud.publish(CLOUD_TOPIC, msg, qos=1)
        print("Sent to EMQX:", msg)

def row(r):
    d = json.loads(r[2]); d.update(ts=r[0], room=r[1]); return d

app = Flask(__name__)

@app.after_request
def cors(r):
    r.headers["Access-Control-Allow-Origin"] = "*"; return r

@app.route("/api/latest")
def latest():
    with lock:
        r = db.execute("SELECT * FROM readings ORDER BY ts DESC LIMIT 1").fetchone()
    return jsonify(row(r) if r else {})

@app.route("/api/history")
def history():
    since = time.time() - float(request.args.get("hours", 24)) * 3600
    with lock:
        rs = db.execute("SELECT * FROM readings WHERE ts > ? ORDER BY ts", (since,)).fetchall()
    return jsonify([row(r) for r in rs])

# Local broker (Mosquitto on the Pi)
client = new_client()
client.on_connect, client.on_message = on_connect, on_message
client.connect("localhost", 1883)
client.loop_start()
app.run(host="0.0.0.0", port=5000)