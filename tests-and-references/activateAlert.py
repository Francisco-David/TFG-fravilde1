import paho.mqtt.client as mqtt
import json
from datetime import datetime

# MQTT CONFIG
BROKER = "192.168.1.145" # "10.129.182.86" #
PORT = 1883
TOPIC = "tfg/sensors/tem"

client = mqtt.Client()
client.connect(BROKER, PORT, 60)

def publish_temperature(value):
    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    message = {
        "sensor": "tem",
        "value": value,
        "timestamp": timestamp
    }

    client.publish(TOPIC, json.dumps(message))
    print(f"Publicado: {message}")

if __name__ == "__main__":
    try:
        publish_temperature(30)  # <-- valor fijo
    finally:
        client.disconnect()