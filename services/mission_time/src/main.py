import os
import time
import json
import yaml
from datetime import datetime, timezone, timedelta
import paho.mqtt.client as mqtt

# Mission Time Service - broadcasts unified mission time via MQTT

MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))

# Load mission configuration
mission_file = os.getenv('MISSION_FILE', '/app/mission.yaml')
with open(mission_file, 'r') as f:
    config = yaml.safe_load(f)

mission_info = config.get('mission', {})
mission_name = mission_info.get('name', 'Unknown Mission')
epoch_str = mission_info.get('epoch', '2025-01-01T00:00:00Z')
time_scale = float(mission_info.get('time_scale', 1.0))
duration_hours = float(mission_info.get('duration_hours', 24.0))

# Parse mission epoch
mission_epoch = datetime.fromisoformat(epoch_str.replace('Z', '+00:00'))
print(f'Mission Time Service starting for: {mission_name}')
print(f'Epoch: {mission_epoch}')
print(f'Time Scale: {time_scale}x')
print(f'Duration: {duration_hours} hours')

client = mqtt.Client()
client.connect(MQTT_BROKER, MQTT_PORT, 60)

# Mission start time (wall clock when we started)
mission_start_wall = time.time()
frequency = 10.0  # Hz - broadcast mission time 10 times per second

while True:
    loop_start = time.time()
    
    # Calculate mission elapsed time
    wall_elapsed = time.time() - mission_start_wall
    mission_elapsed_seconds = wall_elapsed * time_scale
    
    # Current mission time
    current_mission_time = mission_epoch + timedelta(seconds=mission_elapsed_seconds)
    
    # Check if mission is complete
    mission_complete = mission_elapsed_seconds > (duration_hours * 3600)
    
    # Mission time payload
    time_payload = {
        'mission_name': mission_name,
        'mission_epoch': epoch_str,
        'mission_time': current_mission_time.isoformat() + 'Z',
        'mission_elapsed_seconds': mission_elapsed_seconds,
        'time_scale': time_scale,
        'mission_complete': mission_complete,
        'wall_time': datetime.utcnow().isoformat() + 'Z'
    }
    
    # Broadcast on mission/time topic
    client.publish('mission/time', json.dumps(time_payload))
    
    # Also broadcast mission metadata periodically (every 10 seconds)
    if int(wall_elapsed) % 10 == 0:
        metadata_payload = {
            'mission': mission_info,
            'satellites': config.get('satellites', [])
        }
        client.publish('mission/metadata', json.dumps(metadata_payload))
    
    # Sleep for next iteration
    elapsed = time.time() - loop_start
    sleep_time = max(0.0, (1.0 / frequency) - elapsed)
    time.sleep(sleep_time)
