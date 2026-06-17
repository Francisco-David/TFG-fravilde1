import asyncio
import time
from datetime import datetime
import PCF8591 as ADC
import paho.mqtt.client as mqtt
import json
import RPi.GPIO as GPIO
import os
from HUM_SENSOR import read_dht11_dat

# MQTT CONFIG
BROKER = "localhost"
PORT = 1883
TOPIC = "tfg/sensors/"

client = mqtt.Client()
client.connect(BROKER, PORT, 60)
client.loop_start()

# CONFIGURACIÓN SENSORES
ADC.setup(0x48)
GPIO.setmode(GPIO.BCM)

SOUND_PCF8591_PIN = 0
LIGHT_PCF8591_PIN = 1
HUMIDITY_PIN = 16
VIBRATION_PIN = 24
GAS_PIN = 26

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

# FUNCION ASINCRONA PARA POLLING DE SENSORES, CADA UNO CON UN INTERVALO CONFIGURABLE
async def sensor_task(name, interval, channel=None):
    while True:
        if name=="son" or name=="luz":
            try:
                value = ADC.read(channel)
                publish_message(name, value)
            except Exception as e:
                print(f"Error reading {name}: {e}")
            await asyncio.sleep(interval)
            
        elif name=="tem":
            try:
                #global ds18b20
                #for i in os.listdir('/sys/bus/w1/devices'):
                #    if i != 'w1_bus_master1':
                #        ds18b20 = '28-0620157b348c'
                location = '/sys/bus/w1/devices/28-0620157b348c/w1_slave'
                tfile = open(location)
                text = tfile.read()
                tfile.close()
                secondline = text.split("\n")[1]
                temperaturedata = secondline.split(" ")[9]
                temperature = float(temperaturedata[2:])
                value = temperature / 1000
                publish_message(name, round(value, 1))
            except Exception as e:
                print(f"Error reading {name}: {e}")
            await asyncio.sleep(interval)
            
        elif name=="hum":
            try:
                read = read_dht11_dat(channel)
                if read:
                    humidity, temperature = read
                    value = humidity
                    publish_message(name, value)
            except Exception as e:
                print(f"Error reading {name}: {e}")
            await asyncio.sleep(interval)
            
        elif name=="vib":
            try:
                GPIO.setup(channel, GPIO.IN) # pull_up_down=GPIO.PUD_UP)    # Set BtnPin's mode is input, and pull up to high level(3.3V)
                value = GPIO.input(channel)
                publish_message(name, value)
            except Exception as e:
                print(f"Error reading {name}: {e}")
            await asyncio.sleep(interval)
            
        elif name=="gas":
            try:    
                GPIO.setup(channel, GPIO.IN)
                value = GPIO.input(channel)
                publish_message(name, value)
            except Exception as e:
                print(f"Error reading {name}: {e}")
            await asyncio.sleep(interval)


async def main():
    tasks = [
        sensor_task("tem", TEMPERATURE_INTERVAL),
        sensor_task("son", SOUND_INTERVAL, SOUND_PCF8591_PIN),
        sensor_task("luz", LIGHT_INTERVAL, LIGHT_PCF8591_PIN),
        sensor_task("hum", HUMIDITY_INTERVAL, HUMIDITY_PIN),
        sensor_task("vib", VIBRATION_INTERVAL, VIBRATION_PIN),
        sensor_task("gas", GAS_INTERVAL, GAS_PIN),
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