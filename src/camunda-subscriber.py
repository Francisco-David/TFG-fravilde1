from datetime import datetime
import psycopg2
import json
import paho.mqtt.client as mqtt
from pyzeebe import ZeebeClient, create_insecure_channel
import asyncio
import threading

# Config
PROCESS_ID = "temp-process"
ZEEBE_ADDRESS = "localhost:26500"
BROKER_ADDRESS = "10.198.77.86"
MQTT_PORT = 1883
MQTT_TOPIC = "tfg/sensors/+"  # valor'+' para el siguiente nivel (temp, hum, etc.) y '#' para todo el árbol (tfg/sensors/...)


# Obtener fecha y hora actual para la lógica de sesión
ahora = datetime.now()
# HORA_ACTUAL = ahora.strftime("%H:%M")
# DIA_SEMANA = int(ahora.strftime("%w"))
# FECHA_ACTUAL = ahora.strftime("%Y-%m-%d")
HORA_ACTUAL = "10:50"       # Para pruebas
FECHA_ACTUAL = "2026-05-20" # Para pruebas (miércoles)
DIA_SEMANA = 3              # Para pruebas (lunes=1)


# Background asyncio loop setup
def start_asyncio_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

async_loop = asyncio.new_event_loop()
loop_thread = threading.Thread(target=start_asyncio_loop, args=(async_loop,))
loop_thread.daemon = True
loop_thread.start()


# MQTT Callback
def on_message(client, userdata, msg):
    # print(f"Recibido en {msg.topic}: {msg.payload.decode()}")
    sensorId = msg.topic.split("/")[-1]
    try:
        payload = json.loads(msg.payload.decode())
        value = payload.get("value")
        timestamp = payload.get("timestamp")

        print(f"Sensor: {sensorId} | Valor: {value} | Timestamp: {timestamp}")

        # query_insert_nueva_lectura = """
        # INSERT INTO lectura
        # (sensor_id, valor, timestamp, sesion_id)
        # VALUES (%s, %s, %s, %s)
        # """

        # variables = {"temperature": payload.get("value")}

        # future = asyncio.run_coroutine_threadsafe(
        #     start_camunda_process(variables), async_loop
        # )

        # future.add_done_callback(lambda f: f.result() if f.exception() is None else print(f"Async task failed: {f.exception()}"))

    except Exception as e:
        print(f"Error manejando el mensaje: {e}")

# Async function to start camunda (via Zeebe) process. Create BOTH the channel and the client INSIDE the coroutine.
async def start_camunda_process(variables):
    try:
        channel = create_insecure_channel(grpc_address=ZEEBE_ADDRESS)
        zeebe_client = ZeebeClient(channel)

        print(f"Comenzando el proceso '{PROCESS_ID}' con variables: {variables}")
        await zeebe_client.run_process(PROCESS_ID, variables)
        print("Proceso iniciado correctamente.")
    except Exception as e:
        print(f"[ERROR] No se pudo iniciar el proceso de Camunda: {e}")



conn = psycopg2.connect(
    host="localhost",
    database="fravilde1_tfg",
    user="postgres",
    # password="admin"
)
cur = conn.cursor()


print("- BIENVENIDO: " + f"{FECHA_ACTUAL} | {HORA_ACTUAL} -")
aula = input("Introduce el aula (p.e A0.12): ")


# BUSCAR HORARIO ACTIVO
query_encontrar_sesion = """
SELECT horario_id
FROM horario
WHERE aula = %s
AND dia_semana = %s
AND %s BETWEEN hora_inicio AND hora_fin
"""

cur.execute(query_encontrar_sesion, (aula, DIA_SEMANA, HORA_ACTUAL))
sesion_horario = cur.fetchone()

if sesion_horario is None:
    print("No hay clase programada actualmente en ese aula. Sesión no creada.")
else:
    horario_id = sesion_horario[0]

    #Comprobar si ya hay una sesión con ese horario_id y dia actual
    query_comprobar_sesion = """
    SELECT sesion_id
    FROM sesion
    WHERE horario_id = %s
    AND fecha = %s
    """

    cur.execute(query_comprobar_sesion, (horario_id, FECHA_ACTUAL))
    sesion_en_curso = cur.fetchone()

    if sesion_en_curso is not None:

        sesion_id = sesion_en_curso[0]
        print("Ya existe una sesión (ID: {}) para este horario y fecha. Se actualizará su estado a 'en_curso'.".format(sesion_id))

        query_update_sesion = """
        UPDATE sesion
        SET estado = %s
        WHERE sesion_id = %s
        """
        cur.execute(query_update_sesion, ("en_curso", sesion_id))
        
    else:
        #Creamos la sesión y obtenemos su ID
        query_insert_nueva_sesion = """
        INSERT INTO sesion
        (horario_id, fecha, comienza, estado)
        VALUES (%s, %s, NOW()::time(0), %s)
        RETURNING sesion_id
        """

        cur.execute(query_insert_nueva_sesion, (
            horario_id,
            FECHA_ACTUAL,
            "en_curso"
        ))
        sesion_id = cur.fetchone()[0]

    conn.commit()

    print(f"Sesión creada/iniciada correctamente. ID: {sesion_id}\n\n  -  Usa Ctrl+C para detener el suscriptor y finalizar la sesión.\n")

# Cerrar cursor, la conexión se mantendrá abierta para el resto del programa
cur.close()

# MQTT Config
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2) #Error al ejecutar: [Callback API version 1 is deprecated, update to latest version]
mqtt_client.on_message = on_message
mqtt_client.connect(BROKER_ADDRESS, MQTT_PORT, 60)
mqtt_client.subscribe(MQTT_TOPIC)

print(f"Suscrito a topic '{MQTT_TOPIC}'. Esperando mensajes...")


# Gestion de cerrado de sesion y desconexión MQTT
try:
    mqtt_client.loop_forever()
except KeyboardInterrupt:
    print("\nApagando...")
finally:
    # Al finalizar, actualizar el estado de la sesión a "finalizada"
    cur = conn.cursor()

    query_update_sesion = """
    UPDATE sesion
    SET estado = %s, finaliza = now()::time(0)
    WHERE sesion_id = %s
    """

    cur.execute(query_update_sesion, ("finalizada", sesion_id))
    conn.commit()
    print(f"Sesión con ID {sesion_id} finalizada.")

    cur.close()
    conn.close()

    # Detener MQTT y el loop de asyncio
    mqtt_client.disconnect()
    if async_loop.is_running():
        async_loop.call_soon_threadsafe(async_loop.stop)
    print("Apagado completo.")