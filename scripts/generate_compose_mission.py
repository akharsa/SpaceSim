#!/usr/bin/env python3
"""
Generate a docker-compose override that adds satellite services for missions with >2 satellites.
Writes to infrastructure/compose.mission.yml
Usage: generate_compose_mission.py <mission-name>

This keeps the base compose (which defines satellite and satellite-2) and adds satellite-3..N
so each replica gets SAT_ID set appropriately and mounts the canonical mission file.
All satellite services will reference a single common image tag so Compose builds one image.
"""
import sys
import yaml
from pathlib import Path
import os

if len(sys.argv) < 2:
    print("Usage: generate_compose_mission.py <mission-name>")
    sys.exit(2)

mission_name = sys.argv[1]
mission_file = Path('missions') / f"{mission_name}.yaml"
if not mission_file.exists():
    print(f"Mission file {mission_file} not found")
    sys.exit(1)

with mission_file.open() as f:
    mission = yaml.safe_load(f)

sats = mission.get('satellites', [])
count = len(sats)

# project name used in image/container_name; prefer COMPOSE_PROJECT_NAME if set else repo folder name
project_raw = os.environ.get('COMPOSE_PROJECT_NAME', Path('.').resolve().name)
project = project_raw.lower()
image_tag = f"{project}-satellite:latest"

# Build override without a top-level 'version' key to avoid compose warnings
override = {'services': {}}

# Override base satellite services to use the common image (prevents Compose building multiple images)
override['services']['satellite'] = {'image': image_tag}
override['services']['satellite-2'] = {'image': image_tag}

# Generate additional services (satellite-3..N) referencing the same image
for i in range(3, count+1):
    svc_name = f"satellite-{i}"
    override['services'][svc_name] = {
        'image': image_tag,
        'container_name': f"{project}-satellite-{i}",
        'depends_on': ['mosquitto'],
        'environment': [
            'MQTT_BROKER=mosquitto',
            'MQTT_PORT=1883',
            'TIME_SCALE=1.0',
            f'SAT_ID={i}',
        ],
        'volumes': [f'../missions/{mission_name}.yaml:/app/mission.yaml:ro'],
    }

out_path = Path('infrastructure') / 'compose.mission.yml'
with out_path.open('w') as f:
    yaml.safe_dump(override, f, sort_keys=False)

print(f"Wrote override compose to {out_path} with {max(0,count-2)} extra satellite services (image={image_tag})")
