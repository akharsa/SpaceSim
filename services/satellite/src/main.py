import os
import time
import json
import math
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
import numpy as np

# Simple realtime/timewarp satellite publisher (lightweight, no astropy/poliastro)

MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
TIME_SCALE = float(os.getenv('TIME_SCALE', '1.0'))  # 1.0 = realtime, >1 faster

client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)

publish_topic = 'satellite/1/telemetry'
print('Satellite simulator starting, publishing to', publish_topic)

# Simple circular orbit parameters
RE = 6378.137  # Earth radius km
alt_km = 500.0
a = RE + alt_km
mu = 398600.4418  # Earth gravitational parameter km^3/s^2
n = math.sqrt(mu / (a ** 3))  # rad/s mean motion

sim_t = 0.0  # seconds since epoch
frequency = 1.0  # Hz wall clock

while True:
    loop_start = time.time()
    wall_dt = 1.0 / frequency
    sim_t += wall_dt * TIME_SCALE

    # simple circular position in orbital plane
    theta = n * sim_t
    x = a * math.cos(theta)
    y = a * math.sin(theta)
    z = 0.0
    vx = -a * n * math.sin(theta)
    vy = a * n * math.cos(theta)
    vz = 0.0

    battery = max(0.0, 95.0 - sim_t * 0.0001)
    attitude_q = [1.0, 0.0, 0.0, 0.0]

    payload = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'position_km': [x, y, z],
        'velocity_km_s': [vx, vy, vz],
        'battery_pct': battery,
        'attitude_q': attitude_q,
    }

    client.publish(publish_topic, json.dumps(payload))

    elapsed = time.time() - loop_start
    sleep_time = max(0.0, wall_dt - elapsed)
    time.sleep(sleep_time)
