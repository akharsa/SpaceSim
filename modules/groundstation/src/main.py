import os
import json
import time

import paho.mqtt.client as mqtt
from influxdb_client import InfluxDBClient, Point, WritePrecision

MQTT_BROKER = os.getenv('MQTT_BROKER', 'localhost')
MQTT_PORT = int(os.getenv('MQTT_PORT', '1883'))
INFLUX_URL = os.getenv('INFLUX_URL', 'http://localhost:8086')
INFLUX_ORG = os.getenv('INFLUX_ORG', 'org')
INFLUX_BUCKET = os.getenv('INFLUX_BUCKET', 'telemetry')
INFLUX_TOKEN = os.getenv('INFLUX_TOKEN', 'token')

influx = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = influx.write_api()


def on_connect(client, userdata, flags, rc, properties=None):
    print('Connected to MQTT, subscribing to satellite telemetry')
    client.subscribe('satellite/+/telemetry')


client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload)
        # write to influx using wall clock time for Grafana compatibility
        p = Point('satellite')
        p.tag('sat_id', msg.topic.split('/')[1])
        
        # Add satellite name and orbital info as tags for better filtering
        if 'name' in payload:
            p.tag('sat_name', payload['name'])
        
        # Core telemetry fields
        p.field('battery_pct', float(payload.get('battery_pct', 0)))
        p.field('pos_x_km', float(payload['position_km'][0]))
        p.field('pos_y_km', float(payload['position_km'][1]))
        p.field('pos_z_km', float(payload['position_km'][2]))
        
        # Velocity fields
        if 'velocity_km_s' in payload:
            p.field('vel_x_km_s', float(payload['velocity_km_s'][0]))
            p.field('vel_y_km_s', float(payload['velocity_km_s'][1]))
            p.field('vel_z_km_s', float(payload['velocity_km_s'][2]))
        
        # Mission time and orbital elements as fields
        if 'mission_elapsed_seconds' in payload:
            p.field('mission_elapsed_s', float(payload['mission_elapsed_seconds']))
        
        if 'orbital_elements' in payload:
            orb = payload['orbital_elements']
            if 'alt_km' in orb:
                p.field('altitude_km', float(orb['alt_km']))
            if 'true_anom_deg' in orb:
                p.field('true_anomaly_deg', float(orb['true_anom_deg']))
        
        # Use wall timestamp for Grafana time-series compatibility
        # This ensures data appears in Grafana at the correct wall-clock time
        timestamp_field = payload.get('wall_timestamp', payload.get('timestamp'))
        if timestamp_field:
            p.time(timestamp_field, WritePrecision.S)
        else:
            # Fallback to current time if no timestamp available
            p.time(time.time_ns(), WritePrecision.NS)
            
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=p)
        print(f"Wrote telemetry for {payload.get('name', msg.topic.split('/')[1])}")
    except Exception as e:
        print('Error processing message', e, 'Payload:', payload)


client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_forever()
