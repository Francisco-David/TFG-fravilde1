from datetime import datetime
import database
import psycopg2
from psycopg2 import pool
import json
import paho.mqtt.client as mqtt
from pyzeebe import ZeebeClient, create_insecure_channel
import asyncio
import threading
import logging
import os

# CONFIGURACIÓN SCRIPT PYTHON
ZEEBE_ADDRESS = "localhost:26500"
BROKER_ADDRESS = "10.129.182.86" #"192.168.1.145" 
MQTT_PORT = 1883
MQTT_TOPIC = "tfg/sensors/+"  # valor'+' para el siguiente nivel (temp, hum, etc.) y '#' para todo el árbol (tfg/sensors/...)
LOGS_DIR = "I:/UNIVERSIDAD/TFG/TFG-fravilde1/logs"

logger = logging.getLogger(__name__)

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
    sensorId = msg.topic.split("/")[-1]  # El sensorId lo obtenemos del topic MQTT "tfg/sensors/{sensorId}"

    sesion_id = userdata.get("sesion_id")
    conn = None

    # Lectura de valor y timestamp del mensaje MQTT (message = {"sensor": name, "value": value, "timestamp": timestamp})
    payload = json.loads(msg.payload.decode())
    value = payload.get("value")
    timestamp = payload.get("timestamp")
    try:
        conn = database.get_conn()  # Obtenemos una conexión del pool para insertar la lectura
        tipo_sensor = database.find_sensor_tipo(conn, sensorId) # Tipo sensor para saber como procesar la lectura
        if tipo_sensor in ["mixto", "ambiental"]:
            database.insert_lectura(conn, sensorId, value, timestamp, sesion_id)
        elif tipo_sensor == 'alarma':
            # no nos son necesarios los datos de sus medias, sobretodo los de las alarmas.
            pass

        else:
            logger.warning(f"[MQTT] Sensor desconocido: ID '{sensorId}' de tipo '{tipo_sensor}'. No se ha procesado el mensaje.")
            return

    except Exception as e:
        try:
            conn.rollback()  # Si ha habido un error al insertar la lectura en la base de datos, hacemos rollback para evitar dejar la conexión en un estado inconsistente.
                            #   Asi si el error no es de base de datos, evitamos que el programa caiga por un error que no se puede manejar.
        except:
            pass
        logger.error(f"[MQTT] ERROR: {e}")
    finally:
        if conn is not None:
            database.put_conn(conn)  # Devolvemos la conexión al pool para que pueda ser reutilizada por otros hilos o procesos

# FUNCION ASÍNCRONA PARA LAS LLAMADAS A CAMUNDA (VIA ZEEBE)
async def comenzar_proceso_camunda_async(process_id, variables):
    channel = create_insecure_channel(grpc_address=ZEEBE_ADDRESS)
    zeebe_client = ZeebeClient(channel)
    try:
        logger.info(f"[ZEEBE] Comenzando el proceso '{process_id}' con variables: {variables}")
        await zeebe_client.run_process(process_id, variables)
        logger.info(f"[ZEEBE] Proceso '{process_id}' iniciado correctamente.")
    except Exception as e:
        logger.error(f"[ZEEBE] ERROR No se pudo iniciar el proceso '{process_id}' de Camunda: {e}")

# FUNCION PARA INICIAR PROCESOS DE CAMUNDA
def crear_proceso_camunda(async_loop, process_id, variables):
    future = asyncio.run_coroutine_threadsafe(
        comenzar_proceso_camunda_async(process_id, variables),
        async_loop
    )
    future.add_done_callback(lambda fut: camunda_callback(fut, process_id))

# FUNCION QUE SE EJECUTA CUANDO LA COROUTINE DE CAMUNDA TERMINA, PARA REGISTRAR ERRORES O INSPECCIONAR RESULTADOS
def camunda_callback(fut, process_id):
    exc = fut.exception()
    if exc:
        logger.error(f"[ZEEBE] ERROR Error al iniciar proceso async (ID: {process_id}): {exc}")
    else:
        res = fut.result()
        if res is not None:
            logger.info(f"[ZEEBE] Resultado de inicio (ID: {process_id}): {res}")

# FUNCION PARA INICIAR SESIÓN: PIDE EL AULA, BUSCA EL HORARIO CORRESPONDIENTE Y CREA LA SESIÓN EN LA BASE DE DATOS, SI EXISTE LA PONE EN CURSO, SI NO EXISTE LA CREA Y LA PONE EN CURSO
def iniciar_sesion(conn):
    while True:
        aula = input("\t · Introduzca el aula (p.e A0.12):").strip()

        # Buscar el horario que corresponda al aula, día de la semana y hora actual
        sesion_horario = database.find_horario(conn, aula, DIA_SEMANA, HORA_ACTUAL)

        if sesion_horario is None:
            logger.warning("No hay clase programada actualmente en ese aula. Sesión no creada. Inténtalo de nuevo.")
        else:
             break

    horario_id = sesion_horario[0]
    #Comprobar si ya hay una sesión con ese horario_id y dia actual
    sesion_en_curso = database.find_sesion(conn, horario_id, FECHA_ACTUAL)

    if sesion_en_curso is not None:
        #Solo puede haber una sesión en curso por horario_id y fecha, así que cogemos la primera (y única) que encontremos
        sesion_id = sesion_en_curso[0]
        database.update_sesion_estado(conn, sesion_id, "en_curso")
        logger.info(f"Ya existe una sesión (ID: {sesion_id}) para este horario y fecha. Se ha actualizado su estado a 'en_curso'.\n\n  -  Usa Ctrl+C para detener el suscriptor y finalizar la sesión.\n")

    else:
        #Creamos la sesión y obtenemos su ID
        sesion_id = database.insert_nueva_sesion(conn, horario_id, FECHA_ACTUAL)
        logger.info(f"Sesión creada correctamente. ID: {sesion_id}\n\n  -  Usa Ctrl+C para detener el suscriptor y finalizar la sesión.\n")

    return sesion_id

def main():
    # CONFIGURAR LOGGING
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)
    
    log_file = f"{LOGS_DIR}/main.log"
    
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s [%(levelname)-s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

    # INICIALIZAR POOL DE CONEXIONES A LA BASE DE DATOS
    database.init_pool()

    # CONFIGURACION DE EL LOOP DE ASYNCIO EN UN HILO SEPARADO PARA PODER USARLO DESDE EL CALLBACK DE MQTT
    async_loop = asyncio.new_event_loop()
    loop_thread = threading.Thread(target=start_asyncio_loop, args=(async_loop,))
    loop_thread.daemon = True
    loop_thread.start()

    print("\n-  BIENVENIDO: " + f"{FECHA_ACTUAL} | {HORA_ACTUAL}  - \n\n  -  Use Ctrl+C si desea salir del programa.\n")
    logger.info("-  BIENVENIDO: " + f"{FECHA_ACTUAL} | {HORA_ACTUAL}  - ")
    print("\n  -  Use Ctrl+C si desea salir del programa.\n")
    try:
        conn = database.get_conn()  # Obtenemos una conexión del pool para iniciar la sesión
        try:
            sesion_id = iniciar_sesion(conn)
        finally:
            database.put_conn(conn)

        # INICIAR PROCESO DE EVALUACION AMBIENTE EN CAMUNDA
        variables = {
            "sesion_id": sesion_id
        }
        crear_proceso_camunda(async_loop, "eval-ambiental", variables)

    except KeyboardInterrupt:
        logger.warning("\n Sesión no iniciada. Apagando...")
        return

    # CONEXION MQTT y CONFIGURACION MQTT CLIENTE
    mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    mqtt_client.user_data_set({"sesion_id": sesion_id}) # Pasamos el ID de sesión
    mqtt_client.on_message = on_message
    mqtt_client.connect(BROKER_ADDRESS, MQTT_PORT, 60)
    mqtt_client.subscribe(MQTT_TOPIC)

    logger.info(f"[MQTT] Suscrito a topic '{MQTT_TOPIC}'. Esperando mensajes...")
    
    # INICIAR PROCESO DE EVALUACION SENSORES EN CAMUNDA
    crear_proceso_camunda(async_loop, "eval-sensores", variables)

    # Gestion de cerrado de sesion y desconexión MQTT
    try:
        mqtt_client.loop_forever()
    except KeyboardInterrupt:
        logger.info("Apagando...")
    finally:

        # Al finalizar, actualizar el estado de la sesión a "finalizada"
        if sesion_id is not None:
            conn = database.get_conn()  # Obtenemos una conexión del pool para actualizar el estado de la sesión
            database.update_sesion_estado(conn, sesion_id, "finalizada")
            database.put_conn(conn)  # Devolvemos la conexión al pool
        database.close_all()  # Cerramos todas las conexiones del pool

        # Detener MQTT y el loop de asyncio
        mqtt_client.disconnect()
        logger.info("[MQTT] Desconectado del broker MQTT.")
        if async_loop.is_running():
            async_loop.call_soon_threadsafe(async_loop.stop)
        logger.info("Apagado completo.")

if __name__ == "__main__":
    main()