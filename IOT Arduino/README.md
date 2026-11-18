# System 2 – Smart room box

Part of the Student Housing B.V. project. A sensor box measures the air and
presence in a room and shows it on a touch screen and on the group website.

## How it works
ESP32 → MQTT → Raspberry Pi (Mosquitto) → touch screen dashboard
                                        → logger.py → SQLite + API
                                        → EMQX cloud (bv/rooms/1/readings) → website

## Hardware
- ESP32 dev board
- SCD40 (CO2, temperature, humidity) on I2C: SDA D21, SCL D22
- PIR motion sensor on D14
- LDR + 10 kΩ on D34 (light level)
- LEDs (220 Ω): red D27, yellow D26, green D25 (CO2), white D33 (room light), orange D32 (heating)
- Raspberry Pi with 7" touch screen

## What it does
- CO2 traffic light: green < 800, yellow 800–1200, red > 1200 ppm
- White light on when someone is present AND it is dark; off 30 s after the last motion
- Heating LED on when temperature < target (set on the touch screen); setback to 18.5 °C after 15 min empty
- Readings every 3 s locally, sent to the cloud every 30 s

## Folders
| Path | What |
|---|---|
| `arduino/sens/sens.ino` | ESP32 code |
| `pi/logger.py` | Saves readings in SQLite, API on port 5000, forwards to EMQX |
| `pi/dashboard.html` | Touch screen dashboard (MQTT over WebSockets, port 9001) |
| `pi/mqtt.min.js` | MQTT library used by the dashboard (works offline) |

## Setup
**ESP32**
1. Arduino IDE, install libraries: PubSubClient, Sensirion I2C SCD4x.
2. Fill in WiFi name, WiFi password and the Pi IP in `sens.ino`.
3. Upload.

**Raspberry Pi**
1. `sudo apt install -y mosquitto python3-flask python3-paho-mqtt`
2. Mosquitto: listener 1883 (anonymous) and listener 9001 (websockets).
3. Copy the `pi/` files to the Pi's home folder (`~/`).
4. Fill in the EMQX host, username and password in `logger.py`.
5. Autostart: `crontab -e` → `@reboot sleep 20 && python3 ~/logger.py`
6. Kiosk: `~/.config/labwc/autostart` → `/usr/bin/chromium --kiosk --incognito file:///home/<pi-user>/dashboard.html &`

## API (on the Pi)
- `GET http://<pi-ip>:5000/api/latest` – newest reading
- `GET http://<pi-ip>:5000/api/history?hours=24` – readings of the last 24 h

## Cloud message format
Topic `bv/rooms/1/readings`, every 30 s:
```json
{"co2": 615, "temp": 22.7, "humidity": 34.4}
```