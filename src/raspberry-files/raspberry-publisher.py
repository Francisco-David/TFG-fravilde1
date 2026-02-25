import asyncio
import time
from datetime import datetime
import PCF8591 as ADC
import paho.mqtt.client as mqtt
import json
import RPi.GPIO as GPIO
import os
from HUM_SENSOR import read_dht11_dat

ADC.setup(0x48)
GPIO.setmode(GPIO.BCM)

BROKER = "localhost"
PORT = 1883
TOPIC = "tfg/sensors/"

SOUND_PCF8591_PIN = 0
LIGHT_PCF8591_PIN = 1

HUMIDITY_PIN = 16
VIBRATION_PIN = 24
GAS_PIN = 26

client = mqtt.Client()
client.connect(BROKER, PORT, 60)
client.loop_start()


async def sensor_task(name, interval, channel=None):
    while True:
        if name=="sound" or name=="light":
            try:
                value = ADC.read(channel)
                timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                message = {"sensor": name, "value": value, "timestamp": timestamp}
                client.publish(TOPIC + name, json.dumps(message))
                print(f"Published: {message}")
            except Exception as e:
                print(f"Error reading {name}: {e}")
            await asyncio.sleep(interval)
            
        elif name=="temp":
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
                timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                message = {"sensor": name, "value": round(value,1), "timestamp": timestamp}
                client.publish(TOPIC + name, json.dumps(message))
                print(f"Published: {message}")
            except Exception as e:
                print(f"Error reading {name}: {e}")
            await asyncio.sleep(interval)
            
        elif name=="hum":
            try:
                read = read_dht11_dat(channel)
                if read:
                    humidity, temperature = read
                    value = humidity
                    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                    message = {"sensor": name, "value": value, "timestamp": timestamp}
                    client.publish(TOPIC + name, json.dumps(message))
                    print(f"Published: {message}")
            except Exception as e:
                print(f"Error reading {name}: {e}")
            await asyncio.sleep(interval)
            
        elif name=="vib":
            try:
                GPIO.setup(channel, GPIO.IN, pull_up_down=GPIO.PUD_UP)    # Set BtnPin's mode is input, and pull up to high level(3.3V)
                if GPIO.input(channel)==0:
                    value = "Moved"
                    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                    message = {"sensor": name, "value": value, "timestamp": timestamp}
                    client.publish(TOPIC + name, json.dumps(message))
                    print(f"Published: {message}")
            except Exception as e:
                print(f"Error reading {name}: {e}")
            await asyncio.sleep(interval)
            
        elif name=="gas":
            try:    
                #print (ADC.read(0))
                GPIO.setup(channel, GPIO.IN)
                read = GPIO.input(channel)
                #print(tmp)
                if read==0:
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
        sensor_task("sound", 2, SOUND_PCF8591_PIN),
        sensor_task("light", 10, LIGHT_PCF8591_PIN),
        sensor_task("temp", 2),
        sensor_task("hum", 2, HUMIDITY_PIN),
        sensor_task("vib", 0.5, VIBRATION_PIN),
        sensor_task("gas", 1, GAS_PIN),
    ]
    await asyncio.gather(*tasks, return_exceptions=True)

asyncio.run(main())