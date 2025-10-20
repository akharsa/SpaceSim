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

client = mqtt.Client()

influx = InfluxDBClient(url=INFLUX_URL, token=INFLUX_TOKEN, org=INFLUX_ORG)
write_api = influx.write_api()


def on_connect(client, userdata, flags, rc):
    print('Connected to MQTT, subscribing to satellite telemetry')
    client.subscribe('satellite/+/telemetry')


def on_message(client, userdata, msg):
    try:
        payload = json.loads(msg.payload)
        # write to influx
        p = Point('satellite')
        p.tag('sat_id', msg.topic.split('/')[1])
        p.field('battery_pct', float(payload.get('battery_pct', 0)))
        p.field('pos_x_km', float(payload['position_km'][0]))
        p.field('pos_y_km', float(payload['position_km'][1]))
        p.field('pos_z_km', float(payload['position_km'][2]))
        p.time(payload['timestamp'], WritePrecision.S)
        write_api.write(bucket=INFLUX_BUCKET, org=INFLUX_ORG, record=p)
    except Exception as e:
        print('Error processing message', e)


client.on_connect = on_connect
client.on_message = on_message
client.connect(MQTT_BROKER, MQTT_PORT, 60)
client.loop_forever()
