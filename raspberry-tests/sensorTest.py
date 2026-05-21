import asyncio
import time
from datetime import datetime
import random
import paho.mqtt.client as mqtt
import json

BROKER = "localhost"
PORT = 1883
TOPIC = "tfg/sensors/"

client = mqtt.Client()
client.connect(BROKER, PORT, 60)
client.loop_start()


async def sensor_task(name, interval, channel=None):
    while True:
        if name == "son":
            try:
                value = random.randint(30, 90)
                timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                message = {"value": value, "timestamp": timestamp}
                client.publish(TOPIC + name, json.dumps(message))
                print(f"Published: {message}")
            except Exception as e:
                print(f"Error reading {name}: {e}")
            await asyncio.sleep(interval)

        elif name == "luz":
            try:
                value = random.randint(50, 300)
                timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                message = {"sensor": name, "value": value, "timestamp": timestamp}
                client.publish(TOPIC + name, json.dumps(message))
                print(f"Published: {message}")
            except Exception as e:
                print(f"Error reading {name}: {e}")
            await asyncio.sleep(interval)

        elif name == "tem":
            try:
                value = round(random.uniform(16.0, 32.0), 1)
                timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                message = {"sensor": name, "value": value, "timestamp": timestamp}
                client.publish(TOPIC + name, json.dumps(message))
                print(f"Published: {message}")
            except Exception as e:
                print(f"Error reading {name}: {e}")
            await asyncio.sleep(interval)

        elif name == "hum":
            try:
                value = random.randint(30, 80)
                timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                message = {"sensor": name, "value": value, "timestamp": timestamp}
                client.publish(TOPIC + name, json.dumps(message))
                print(f"Published: {message}")
            except Exception as e:
                print(f"Error reading {name}: {e}")
            await asyncio.sleep(interval)

        elif name == "vib":
            try:
                if random.random() < 0.1:
                    value = "Moved"
                    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                    message = {"sensor": name, "value": value, "timestamp": timestamp}
                    client.publish(TOPIC + name, json.dumps(message))
                    print(f"Published: {message}")
            except Exception as e:
                print(f"Error reading {name}: {e}")
            await asyncio.sleep(interval)

        elif name == "gas":
            try:
                if random.random() < 0.1:
                    value = "Abnormal presence"
                    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                    message = {"sensor": name, "value": value, "timestamp": timestamp}
                    client.publish(TOPIC + name, json.dumps(message))
                    print(f"Published: {message}")
            except Exception as e:
                print(f"Error reading {name}: {e}")
            await asyncio.sleep(interval)


async def main():
    tasks = [
        sensor_task("son", 1),
        sensor_task("luz", 10),
        sensor_task("tem", 2),
        sensor_task("hum", 2),
        sensor_task("vib", 0.5),
        sensor_task("gas", 1),
    ]
    await asyncio.gather(*tasks, return_exceptions=True)


asyncio.run(main())