import paho.mqtt.client as mqtt
import pandas as pd
import csv
from datetime import datetime
import json

FINAL_CSV = "final_merged_sensor_data.csv"
MQTT_BROKER = "192.168.0.11"
MQTT_PORT = 1883
MQTT_TOPIC = "esp32/dht11/data"

try:
    with open(FINAL_CSV, "x", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp", "temperature", "humidity"])
except FileExistsError:
    pass 

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker!")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Failed to connect, return code {rc}")

def on_message(client, userdata, msg):
    raw_message = msg.payload.decode()
    print(f"Received raw message: {raw_message}")

    try:
        data = json.loads(raw_message)
    except json.JSONDecodeError:
        print("Skipped malformed message:", raw_message)
        return

    temp = data.get("temperature")
    hum = data.get("humidity")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if temp is not None and hum is not None:
        with open(FINAL_CSV, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([timestamp, temp, hum])
        print(f"Appended data: {timestamp}, {temp}, {hum}")
    else:
        print("Skipped incomplete data:", raw_message)

client = mqtt.Client()
client.on_connect = on_connect
client.on_message = on_message

client.connect(MQTT_BROKER, MQTT_PORT, 60)
print("Starting MQTT loop...")
client.loop_forever()
