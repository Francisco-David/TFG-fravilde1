from datetime import datetime
import database
import psycopg2
import json
import paho.mqtt.client as mqtt
from pyzeebe import ZeebeClient, create_insecure_channel
import asyncio
import threading

# CONFIGURACIÓN SCRIPT PYTHON
PROCESS_ID = "temp-process"
ZEEBE_ADDRESS = "localhost:26500"
BROKER_ADDRESS = "10.198.77.86"
MQTT_PORT = 1883
MQTT_TOPIC = "tfg/sensors/+"  # valor'+' para el siguiente nivel (temp, hum, etc.) y '#' para todo el árbol (tfg/sensors/...)

# OBTENER AULA, FECHA Y HORA ACTUAL PARA LA LÓGICA DE SESIÓN
ahora = datetime.now()
# HORA_ACTUAL = ahora.strftime("%H:%M")
# DIA_SEMANA = int(ahora.strftime("%w"))
# FECHA_ACTUAL = ahora.strftime("%Y-%m-%d")
HORA_ACTUAL = "10:50"       # Para pruebas
FECHA_ACTUAL = "2026-05-20" # Para pruebas (miércoles)
DIA_SEMANA = 3              # Para pruebas (lunes=1)


# LOOP DE ASYNCIO EN BACKGROUND PARA CAMUNDA
def start_asyncio_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()


# MQTT ON MESSAGE CALLBACK
def on_message(client, userdata, msg):
    sensorId = msg.topic.split("/")[-1]
    sesion_id = userdata.get("sesion_id")
    conn = userdata.get("conn")
    tipo_sensor = database.find_sensor_tipo(conn, sensorId)
    try:
        if tipo_sensor == "ambiental":
            payload = json.loads(msg.payload.decode())
            value = payload.get("value")
            timestamp = payload.get("timestamp")
            database.insert_lectura(conn, sensorId, value, timestamp, sesion_id)
        elif tipo_sensor == "alarma":
            pass
        else:
            print(f"[MQTT] Sensor desconocido '{sensorId}' de tipo '{tipo_sensor}'. No se ha procesado el mensaje.")
            return
        
        # variables = {"temperature": payload.get("value")}

        # future = asyncio.run_coroutine_threadsafe(
        #     start_camunda_process(variables), async_loop
        # )

        # future.add_done_callback(lambda f: f.result() if f.exception() is None else print(f"Async task failed: {f.exception()}"))

    except Exception as e:
        try:
            conn.rollback()  # Si ha habido un error al insertar la lectura en la base de datos, hacemos rollback para evitar dejar la conexión en un estado inconsistente.
                             #   Si el error no es de base de datos, evitamos que el programa caiga por un error que no se puede manejar.
        except:
            pass
        print(f"[MQTT] ERROR: {e}")

# FUNCION ASÍNCRONA PARA LAS LLAMADAS A CAMUNDA (VIA ZEEBE)
async def start_camunda_process(variables):
    try:
        channel = create_insecure_channel(grpc_address=ZEEBE_ADDRESS)
        zeebe_client = ZeebeClient(channel)

        print(f"[ZEEBE] Comenzando el proceso '{PROCESS_ID}' con variables: {variables}")
        await zeebe_client.run_process(PROCESS_ID, variables)
        print("[ZEEBE] Proceso iniciado correctamente.")
    except Exception as e:
        print(f"[ERROR] No se pudo iniciar el proceso de Camunda: {e}")

def iniciar_sesion(conn):
    while True:
        aula = input("\t · Introduzca el aula (p.e A0.12):").strip()

        # Buscar el horario que corresponda al aula, día de la semana y hora actual
        sesion_horario = database.find_horario(conn, aula, DIA_SEMANA, HORA_ACTUAL)
        
        if sesion_horario is None:
            print("[ERROR] No hay clase programada actualmente en ese aula. Sesión no creada. Inténtalo de nuevo.")
        else:
             break
        
    horario_id = sesion_horario[0]
    #Comprobar si ya hay una sesión con ese horario_id y dia actual
    sesion_en_curso = database.find_sesion(conn, horario_id, FECHA_ACTUAL)

    if sesion_en_curso is not None:
        #Solo puede haber una sesión en curso por horario_id y fecha, así que cogemos la primera (y única) que encontremos
        sesion_id = sesion_en_curso[0]
        database.update_sesion_estado(conn, sesion_id, "en_curso")
        print(f"Ya existe una sesión (ID: {sesion_id}) para este horario y fecha. Se ha actualizado su estado a 'en_curso'.\n\n  -  Usa Ctrl+C para detener el suscriptor y finalizar la sesión.\n")
        
    else:
        #Creamos la sesión y obtenemos su ID
        sesion_id = database.insert_nueva_sesion(conn, horario_id, FECHA_ACTUAL)
        print(f"Sesión creada correctamente. ID: {sesion_id}\n\n  -  Usa Ctrl+C para detener el suscriptor y finalizar la sesión.\n")

    return sesion_id
    
def main():
    # CONEXIÓN A LA BASE DE DATOS
    conn = psycopg2.connect(
        host="localhost",
        database="fravilde1_tfg",
        user="postgres",
        # password="admin"
    )

    # CONFIGURACION DE EL LOOP DE ASYNCIO EN UN HILO SEPARADO PARA PODER USARLO DESDE EL CALLBACK DE MQTT
    async_loop = asyncio.new_event_loop()
    loop_thread = threading.Thread(target=start_asyncio_loop, args=(async_loop,))
    loop_thread.daemon = True
    loop_thread.start()

    print("\n-  BIENVENIDO: " + f"{FECHA_ACTUAL} | {HORA_ACTUAL}  - \n\n  -  Use Ctrl+C si desea salir del programa.\n")
    try:
        sesion_id = iniciar_sesion(conn)
    except KeyboardInterrupt:
        print("\n Sesión no iniciada. Apagando...")
        return

    # CONFIGURACION MQTT CLIENTE
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.user_data_set({"sesion_id": sesion_id, "conn": conn}) # Pasamos el ID de sesión y la conexión a la base de datos al callback de MQTT
    mqtt_client.on_message = on_message
    mqtt_client.connect(BROKER_ADDRESS, MQTT_PORT, 60)
    mqtt_client.subscribe(MQTT_TOPIC)

    print(f"[MQTT] Suscrito a topic '{MQTT_TOPIC}'. Esperando mensajes...")


    # Gestion de cerrado de sesion y desconexión MQTT
    try:
        mqtt_client.loop_forever()
    except KeyboardInterrupt:
        print("\nApagando...")
    finally:
        # Al finalizar, actualizar el estado de la sesión a "finalizada"
        if sesion_id is not None:
            database.update_sesion_estado(conn, sesion_id, "finalizada")
        conn.close()

        # Detener MQTT y el loop de asyncio
        mqtt_client.disconnect()
        print("[MQTT] Desconectado del broker MQTT.")
        if async_loop.is_running():
            async_loop.call_soon_threadsafe(async_loop.stop)
        print("Apagado completo.")

if __name__ == "__main__":
    main()