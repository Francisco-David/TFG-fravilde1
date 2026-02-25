import time
import paho.mqtt.client as mqtt
import random  # Simula datos de sensores

# import RPi.GPIO as GPIO
import time
import threading

# Setup GPIO
PIR_PIN = 17  # Pin connected to PIR sensor
LED_PIN = 18  # Pin connected to LED or buzzer

# GPIO.setmode(GPIO.BCM)
# GPIO.setup(PIR_PIN, GPIO.IN)
# GPIO.setup(LED_PIN, GPIO.OUT)


# Configuración del Broker MQTT
BROKER = "localhost"  # Dirección del broker (localhost para la Raspberry Pi misma)
PORT = 1883  # Puerto MQTT estándar
TOPIC = "home/sensors/motion"  # Tema para los datos del sensor

# Conectar al broker
client = mqtt.Client()
client.connect(BROKER, PORT, 60)
client.loop_start()

# Publicar datos simulados del sensor
try:
    while True:
#        if GPIO.input(PIR_PIN):  # Motion detected
        if True:  # Motion detected
            # Simular detección de movimiento
            motion_detected = random.choice([True, False])  # True o False aleatoriamente
            message = {"motion": motion_detected}
            client.publish(TOPIC, str(message))
            print(f"Publicado: {message} en el tema {TOPIC}")
            time.sleep(2)  # Enviar datos cada 2 segundos
        else:
            motion_state["detected"] = False
            GPIO.output(LED_PIN, GPIO.LOW)  # Turn off LED/Buzzer

except KeyboardInterrupt:
    print("Finalizando...")
finally:
    client.disconnect()
