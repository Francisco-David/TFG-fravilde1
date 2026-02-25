import paho.mqtt.client as mqtt

# Configuración del Broker MQTT
BROKER = "10.245.208.86"  # Dirección IP de la Raspberry Pi

PORT = 1883
TOPIC = "tfg/sensors/+"

# Función para manejar mensajes recibidos
def on_message(client, userdata, msg):
    print(f"{msg.topic}: {msg.payload.decode()}")

# Conectar al broker y suscribirse al tema
client = mqtt.Client()
client.on_message = on_message
client.connect(BROKER, PORT, 60)
client.subscribe(TOPIC)

print(f"Suscrito al tema {TOPIC}. Esperando mensajes...")
try:
    client.loop_forever()
except KeyboardInterrupt:
    print("Finalizando...")
finally:
    client.disconnect()

# # Flask route
# @app.route("/")
# def index():
#     return render_template("motion.html", motion=motion_state["detected"])

# # Start motion monitoring thread
# motion_thread = threading.Thread(target=monitor_motion, daemon=True)
# motion_thread.start()

# # Run Flask app
# if __name__ == "__main__":
#     try:
#         app.run(host="0.0.0.0", port=5000)
#     except KeyboardInterrupt:
#         print("Stopping...")
#     finally:
#         # GPIO.cleanup()
#         print("Finally")