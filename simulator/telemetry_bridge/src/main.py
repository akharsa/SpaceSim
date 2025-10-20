import os
import json
import time
from flask import Flask, jsonify
import threading
import paho.mqtt.client as mqtt

app = Flask(__name__)
LATEST = {}
LAST_SEEN = {}
MISSION_TIME = {}
TOPIC = os.getenv('TELEMETRY_TOPIC', 'satellite/+/telemetry')
MQTT_BROKER = os.getenv('MQTT_BROKER', 'mosquitto')
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
SATELLITE_TIMEOUT_SECONDS = 10  # Remove satellites after 10 seconds of no data


def cleanup_stale_satellites():
    """Remove satellites that haven't been seen recently"""
    now = time.time()
    stale_satellites = []
    
    for sat_id, last_seen_time in LAST_SEEN.items():
        if now - last_seen_time > SATELLITE_TIMEOUT_SECONDS:
            stale_satellites.append(sat_id)
    
    for sat_id in stale_satellites:
        print(f"Removing stale satellite: {sat_id}")
        if sat_id in LATEST:
            del LATEST[sat_id]
        if sat_id in LAST_SEEN:
            del LAST_SEEN[sat_id]


@app.route('/telemetry')
def telemetry():
    cleanup_stale_satellites()
    return jsonify(list(LATEST.values()))


@app.route('/mission-time')
def mission_time():
    return jsonify(MISSION_TIME)


def on_connect(client, userdata, flags, rc):
    print('Telemetry bridge connected to MQTT')
    client.subscribe('satellite/+/telemetry')
    client.subscribe('mission/time')
    client.subscribe('mission/metadata')


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload.decode())
    except Exception:
        return
        
    if msg.topic == 'mission/time':
        MISSION_TIME.update(payload)
    elif msg.topic == 'mission/metadata':
        MISSION_TIME['metadata'] = payload
    else:
        # Satellite telemetry
        parts = msg.topic.split('/')
        sat_id = parts[1] if len(parts) > 1 else 'unknown'
        payload['sat_id'] = sat_id
        # Add mission time info if available
        if MISSION_TIME:
            payload['time_scale'] = MISSION_TIME.get('time_scale', 1.0)
        
        # Update satellite data and timestamp
        LATEST[sat_id] = payload
        LAST_SEEN[sat_id] = time.time()


def mqtt_thread():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.loop_forever()


if __name__ == '__main__':
    t = threading.Thread(target=mqtt_thread, daemon=True)
    t.start()
    app.run(host='0.0.0.0', port=5000)
