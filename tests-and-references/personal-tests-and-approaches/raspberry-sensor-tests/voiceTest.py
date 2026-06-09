import PCF8591 as ADC
import RPi.GPIO as GPIO
import time
import paho.mqtt.client as mqtt

GPIO.setmode(GPIO.BCM)

# Configuración del Broker MQTT
BROKER = "localhost"  # Dirección del broker (localhost para la Raspberry Pi misma)
PORT = 1883  # Puerto MQTT estándar
TOPIC = "tfg/sensors/"  # Tema para los datos del sensor

# Conectar al broker
client = mqtt.Client()
client.connect(BROKER, PORT, 60)
client.loop_start()

def setup():
    ADC.setup(0x48)

def loop():
    while True:
        voiceValue = ADC.read(0)
        if voiceValue:
            pub = TOPIC+"sound"
            message = {"Sound: ": voiceValue}
            client.publish(pub, str(message))
            print(f"Publicado: {message} en el tema {pub}")
            time.sleep(0.1)

if __name__ == '__main__':
    try:
        setup()
        loop()
    except KeyboardInterrupt:
        pass
