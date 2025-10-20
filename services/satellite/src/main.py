import os
import time
import json
import math
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
import numpy as np
import yaml

# Simple realtime/timewarp satellite publisher (lightweight, no astropy/poliastro)

MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
TIME_SCALE = float(os.getenv('TIME_SCALE', '1.0'))  # 1.0 = realtime, >1 faster

client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Satellite identifier (can be set per-container via SAT_ID env var)
SAT_ID = os.getenv('SAT_ID', '1')
publish_topic = f'satellite/{SAT_ID}/telemetry'
print('Satellite simulator starting, publishing to', publish_topic)

# Read initial parameters from environment (configured at build time)
# Set these in your Dockerfile or docker-compose for each satellite instance.
alt_env = os.getenv('ALT_KM')
inc_env = os.getenv('INC_DEG')

if alt_env is not None and inc_env is not None:
    alt_km = float(alt_env)
    inc_deg = float(inc_env)
    print('Configured from env SAT_ID', SAT_ID, 'alt_km=', alt_km, 'inc_deg=', inc_deg)
else:
    # Try to load canonical mission file from repo root (mounted into container via compose)
    mission_file = os.getenv('MISSION_FILE', '/app/mission.yaml')
    try:
        with open(mission_file, 'r') as f:
            mission = yaml.safe_load(f)
        sat_cfg = next((s for s in mission.get('satellites', []) if str(s.get('sat_id')) == str(SAT_ID)), None)
        if sat_cfg:
            alt_km = float(sat_cfg.get('initial', {}).get('alt_km', 500.0))
            inc_deg = float(sat_cfg.get('initial', {}).get('inc_deg', 0.0))
            print('Loaded mission SAT_ID', SAT_ID, 'alt_km=', alt_km, 'inc_deg=', inc_deg)
        else:
            print('No mission entry for SAT_ID', SAT_ID, '- using defaults')
            alt_km = 500.0
            inc_deg = 0.0
    except Exception as e:
        print('Failed to load mission file', mission_file, e)
        alt_km = 500.0
        inc_deg = 0.0

# Simple circular orbit parameters
RE = 6378.137  # Earth radius km
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
