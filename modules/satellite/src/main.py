import os
import time
import json
import math
from datetime import datetime, timezone

import paho.mqtt.client as mqtt
import numpy as np
import yaml

# Synchronized satellite simulator using mission time service

MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))

# Mission time state (updated via MQTT subscription)
mission_time_state = {
    'mission_elapsed_seconds': 0.0,
    'mission_time': None,
    'time_scale': 1.0,
    'synchronized': False
}

def on_message(client, userdata, msg):
    """Handle incoming mission time messages"""
    if msg.topic == 'mission/time':
        try:
            time_data = json.loads(msg.payload.decode())
            mission_time_state.update({
                'mission_elapsed_seconds': time_data['mission_elapsed_seconds'],
                'mission_time': time_data['mission_time'],
                'time_scale': time_data['time_scale'],
                'synchronized': True
            })
        except Exception as e:
            print(f'Failed to parse mission time: {e}')

client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.subscribe('mission/time')
client.loop_start()  # Start background thread for MQTT

# Satellite identifier (can be set per-container via SAT_ID env var)
SAT_ID = os.getenv('SAT_ID', '1')
publish_topic = f'satellite/{SAT_ID}/telemetry'
print('Satellite simulator starting, publishing to', publish_topic)

# Read initial parameters from environment (configured at build time)
# Set these in your Dockerfile or docker-compose for each satellite instance.
alt_env = os.getenv('ALT_KM')
inc_env = os.getenv('INC_DEG')

sat_name = f'SAT-{SAT_ID}'  # default name

if alt_env is not None and inc_env is not None:
    alt_km = float(alt_env)
    inc_deg = float(inc_env)
    raan_deg = 0.0
    argp_deg = 0.0
    true_anom_deg = 0.0
    print('Configured from env SAT_ID', SAT_ID, 'alt_km=', alt_km, 'inc_deg=', inc_deg)
else:
    # Try to load canonical mission file from repo root (mounted into container via compose)
    mission_file = os.getenv('MISSION_FILE', '/app/mission.yaml')
    try:
        with open(mission_file, 'r') as f:
            mission = yaml.safe_load(f)
        sat_cfg = next((s for s in mission.get('satellites', []) if str(s.get('sat_id')) == str(SAT_ID)), None)
        if sat_cfg:
            initial = sat_cfg.get('initial', {})
            alt_km = float(initial.get('alt_km', 500.0))
            inc_deg = float(initial.get('inc_deg', 0.0))
            raan_deg = float(initial.get('raan_deg', 0.0))
            argp_deg = float(initial.get('argp_deg', 0.0))
            true_anom_deg = float(initial.get('true_anom_deg', 0.0))
            sat_name = sat_cfg.get('name', f'SAT-{SAT_ID}')
            
            # Also get mission info for synchronization
            mission_info = mission.get('mission', {})
            mission_name = mission_info.get('name', 'Unknown Mission')
            print(f'Loaded {mission_name}: {sat_name} (SAT_ID {SAT_ID}): alt={alt_km}km, inc={inc_deg}°, raan={raan_deg}°, true_anom={true_anom_deg}°')
        else:
            print('No mission entry for SAT_ID', SAT_ID, '- using defaults')
            alt_km = 500.0
            inc_deg = 0.0
            raan_deg = 0.0
            argp_deg = 0.0
            true_anom_deg = 0.0
    except Exception as e:
        print('Failed to load mission file', mission_file, e)
        alt_km = 500.0
        inc_deg = 0.0
        raan_deg = 0.0
        argp_deg = 0.0
        true_anom_deg = 0.0

# Convert degrees to radians
inc_rad = math.radians(inc_deg)
raan_rad = math.radians(raan_deg)
argp_rad = math.radians(argp_deg)
true_anom_0_rad = math.radians(true_anom_deg)

# Simple circular orbit parameters
RE = 6378.137  # Earth radius km
a = RE + alt_km
mu = 398600.4418  # Earth gravitational parameter km^3/s^2
n = math.sqrt(mu / (a ** 3))  # rad/s mean motion

def orbital_to_ecef(theta, inc, raan, argp):
    """Convert orbital plane coordinates to ECEF coordinates"""
    # Position in orbital plane
    x_orb = a * math.cos(theta)
    y_orb = a * math.sin(theta)
    z_orb = 0.0
    
    # Velocity in orbital plane
    vx_orb = -a * n * math.sin(theta)
    vy_orb = a * n * math.cos(theta)
    vz_orb = 0.0
    
    # Rotation matrices for orbital mechanics transformations
    # Rotate by argument of perigee (around z-axis)
    cos_argp, sin_argp = math.cos(argp), math.sin(argp)
    x1 = x_orb * cos_argp - y_orb * sin_argp
    y1 = x_orb * sin_argp + y_orb * cos_argp
    z1 = z_orb
    
    vx1 = vx_orb * cos_argp - vy_orb * sin_argp
    vy1 = vx_orb * sin_argp + vy_orb * cos_argp
    vz1 = vz_orb
    
    # Rotate by inclination (around x-axis)
    cos_inc, sin_inc = math.cos(inc), math.sin(inc)
    x2 = x1
    y2 = y1 * cos_inc - z1 * sin_inc
    z2 = y1 * sin_inc + z1 * cos_inc
    
    vx2 = vx1
    vy2 = vy1 * cos_inc - vz1 * sin_inc
    vz2 = vy1 * sin_inc + vz1 * cos_inc
    
    # Rotate by RAAN (around z-axis)
    cos_raan, sin_raan = math.cos(raan), math.sin(raan)
    x_ecef = x2 * cos_raan - y2 * sin_raan
    y_ecef = x2 * sin_raan + y2 * cos_raan
    z_ecef = z2
    
    vx_ecef = vx2 * cos_raan - vy2 * sin_raan
    vy_ecef = vx2 * sin_raan + vy2 * cos_raan
    vz_ecef = vz2
    
    return [x_ecef, y_ecef, z_ecef], [vx_ecef, vy_ecef, vz_ecef]

# Wait for mission time synchronization
print('Waiting for mission time synchronization...')
while not mission_time_state['synchronized']:
    time.sleep(0.1)
print('Mission time synchronized!')

frequency = 1.0  # Hz wall clock

while True:
    loop_start = time.time()
    wall_dt = 1.0 / frequency  # Define wall clock delta time
    
    # Use mission elapsed time instead of local simulation time
    if not mission_time_state['synchronized']:
        print('Lost mission time sync, waiting...')
        time.sleep(1.0)
        continue
        
    mission_elapsed = mission_time_state['mission_elapsed_seconds']
    
    # Current true anomaly = initial + mean motion * mission time
    theta = true_anom_0_rad + n * mission_elapsed
    
    # Convert orbital coordinates to ECEF coordinates
    position_km, velocity_km_s = orbital_to_ecef(theta, inc_rad, raan_rad, argp_rad)

    battery = max(0.0, 95.0 - mission_elapsed * 0.0001)
    attitude_q = [1.0, 0.0, 0.0, 0.0]

    # Satellite operational status simulation
    satellite_uptime = mission_elapsed  # Uptime in seconds since mission start
    
    # Mode simulation based on battery and time
    if battery < 20.0:
        satellite_mode = "fail"
        attitude_mode = "detumbling"
    elif mission_elapsed < 300:  # First 5 minutes
        satellite_mode = "nominal" 
        attitude_mode = "detumbling"
    elif mission_elapsed < 600:  # Next 5 minutes
        satellite_mode = "nominal"
        attitude_mode = "solar_pointing"
    else:
        satellite_mode = "nominal"
        attitude_mode = "nadir_pointing"

    # Add some variation based on satellite ID
    if SAT_ID == "2" and mission_elapsed > 1200:  # Sat-2 has issues after 20 min
        satellite_mode = "fail"
        attitude_mode = "detumbling"

    payload = {
        'sat_id': SAT_ID,
        'name': sat_name,
        'mission_time': mission_time_state['mission_time'],
        'mission_elapsed_seconds': mission_elapsed,
        'wall_timestamp': datetime.utcnow().isoformat() + 'Z',
        'position_km': position_km,
        'velocity_km_s': velocity_km_s,
        'battery_pct': battery,
        'attitude_q': attitude_q,
        'satellite_status': {
            'mode': satellite_mode,
            'attitude_mode': attitude_mode,
            'uptime_seconds': satellite_uptime,
            'health': "nominal" if satellite_mode == "nominal" else "degraded"
        },
        'orbital_elements': {
            'alt_km': alt_km,
            'inc_deg': inc_deg,
            'true_anom_deg': math.degrees(theta) % 360,
            'raan_deg': raan_deg,
            'argp_deg': argp_deg
        }
    }

    client.publish(publish_topic, json.dumps(payload))

    elapsed = time.time() - loop_start
    sleep_time = max(0.0, wall_dt - elapsed)
    time.sleep(sleep_time)
