import asyncio
import time
import random
from datetime import datetime
import paho.mqtt.client as mqtt
import json

# MQTT CONFIG
# BROKER_ADDRESS = "10.129.182.86" # "192.168.1.145" # 
BROKER ="10.129.182.86" # "192.168.1.145" # "localhost" #
PORT = 1883
TOPIC = "tfg/sensors/"

client = mqtt.Client()
client.connect(BROKER, PORT, 60)
client.loop_start()

TEMPERATURE_INTERVAL = 120
SOUND_INTERVAL = 30
LIGHT_INTERVAL = 210
HUMIDITY_INTERVAL = 120
VIBRATION_INTERVAL = 0.5
GAS_INTERVAL = 1


def publish_message(sensor_name, value):
    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    message = {"sensor": sensor_name, "value": value, "timestamp": timestamp}
    client.publish(TOPIC + sensor_name, json.dumps(message))
    print(f"Published: {message}")


# FUNCION ASINCRONA PARA TESTEO, SIMULA EL POLLING DE SENSORES CON VALORES ALEATORIOS CAMBIANTES CON SENTIDO PARA CADA SENSOR
async def sensor_test(name, interval, channel=None):
    while True:
        if name=="son" :
            value = random.randint(249, 260)
            publish_message(name, value)
            await asyncio.sleep(interval)
            
        if name=="luz":
            value = random.randint(20, 60)
            publish_message(name, value)
            await asyncio.sleep(interval)
            
        elif name=="tem":
            value = round(random.uniform(15.0, 30.0), 2)  # Temperatura entre 15 y 30 grados
            publish_message(name, value)
            await asyncio.sleep(interval)
            
        elif name=="hum":
            value = round(random.uniform(30.0, 70.0), 2)  # Humedad entre 30% y 70%
            publish_message(name, value)
            await asyncio.sleep(interval)
            
        elif name=="vib":
            value = random.choice([0, 0])  # Vibración detectada (1) o no detectada (0)
            publish_message(name, value)
            await asyncio.sleep(interval)
            
        elif name=="gas":
            value = random.choice([0, 0])  # Nivel de gas entre 200 y 800 ppm
            publish_message(name, value)
            await asyncio.sleep(interval)


async def main():
    tasks = [
        sensor_test("tem", TEMPERATURE_INTERVAL),
        sensor_test("son", SOUND_INTERVAL),
        sensor_test("luz", LIGHT_INTERVAL),
        sensor_test("hum", HUMIDITY_INTERVAL),
        # sensor_test("vib", VIBRATION_INTERVAL),
        # sensor_test("gas", GAS_INTERVAL),
    ]
    await asyncio.gather(*tasks, return_exceptions=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Interrupción del usuario (Ctrl+C). Limpiando recursos...")
        client.loop_stop()
        try:
            client.disconnect()
        except Exception:
            pass