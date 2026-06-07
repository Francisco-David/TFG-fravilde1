from pyzeebe import ZeebeTaskRouter, Job
import database
from datetime import datetime,timedelta
import logging

router = ZeebeTaskRouter()
logger = logging.getLogger(__name__)


# FUNCIONES BPMN eval-ambiental
@router.task(task_type="leerLecturas")
async def leer_lecturas(job: Job):
    res = {}
    sesion_id = job.variables.get("sesion_id")

    conn = database.get_conn()
    ultimas_lecturas = database.find_ultima_lectura_por_sensor(conn, sesion_id)
    sensores_ambientales = database.find_todos_los_sensores_tipo(conn,'ambiental')
    database.put_conn(conn)
    
    dicc_lecturas = {lectura[0]: lectura for lectura in ultimas_lecturas}  # Creamos un diccionario para acceder a las lecturas por sensor_id
    for sensor in sensores_ambientales:
        estado_sensor = sensor[3]
        if estado_sensor=="operativo":
            nombre_sensor = sensor[0]
            lectura_sensor = dicc_lecturas[nombre_sensor]
            res[f"{nombre_sensor}Valor"] = lectura_sensor[1]
    
    logger.info(f'[CAMUNDA] "leerLecturas" - sesion_id: {sesion_id}\n (lecturas: {res})')
    return res

@router.task(task_type="calculoEvaluacion")
async def calcular_evaluacion(job: Job):
    sesion_id = job.variables.get("sesion_id")
    puntuacion = 80  # Aquí iría la lógica real para calcular la puntuación basada en las lecturas y otros factores

    conn = database.get_conn()
    database.insert_evaluacion(conn, sesion_id, puntuacion)
    database.put_conn(conn)

    logger.info(f'[CAMUNDA] "calculoEvaluacion" - sesion_id: {sesion_id}, puntuacion: {puntuacion}')
    return {'puntuacion': puntuacion}

@router.task(task_type="comprobarEstado")
async def comprobar_estado(job: Job):
    sesion_id = job.variables.get("sesion_id")

    conn = database.get_conn()
    estado_sesion = database.find_estado_sesion(conn, sesion_id)
    database.put_conn(conn)

    logger.info(f'[CAMUNDA] "comprobarEstado" - sesion_id: {sesion_id}, estado: {estado_sesion}')
    return {'estadoSesion': estado_sesion}

#FUNCIONES BPMN eval-sensores
@router.task(task_type="comprobarSensores")
async def comprobar_sensores(job: Job):
    sesion_id = job.variables.get("sesion_id")
    now = datetime.now()

    conn = database.get_conn()
    ultimas_lecturas = database.find_ultima_lectura_por_sensor(conn, sesion_id)
    sensors = database.find_todos_los_sensores(conn)
    
    dicc_lecturas = {lectura[0]: lectura for lectura in ultimas_lecturas}  # Creamos un diccionario para acceder a las lecturas por sensor_id
    sensors_received = list(dicc_lecturas.keys())

    for sensor in sensors:
        nombre_sensor = sensor[0]
        tipo_sensor = sensor[1] 
        validez = sensor[2]
        estado_sensor = sensor[3]
        if nombre_sensor in sensors_received:
            if tipo_sensor in ['mixto', 'ambiental']:
                lectura_sensor = dicc_lecturas[nombre_sensor]
                validez_transmision = (lectura_sensor[2]+timedelta(seconds=validez))>now # Chequeamos que la lectura no sea demasiado antigua sumando el valor de validez del sensor a su timestamp
                if validez_transmision and estado_sensor=='defectuoso':

                    database.update_estado_sensor(conn, nombre_sensor,'operativo')
                    # COMPROBAR SI HAY OK
                    #   SI NO HAY OK METER OK "SE HA RECUPERADO LA CONEXION"
                    # print(f'[CAMUNDA] sensor: {nombre_sensor} operativo\n')

                elif not validez_transmision and estado_sensor=='operativo':

                    database.update_estado_sensor(conn, nombre_sensor,'defectuoso')
                    # COMPROBAR SI HAY ALARMA ACK
                    #   SI NO HAY ALARMA O LA QUE HAY NO ESTÁ ACK METER AVISO "SE HA PERDIDO LA CONEXION"
                    # print(f'[CAMUNDA] sensor: {nombre_sensor} defectuoso\n')

            else: # Se ha recibido una lectura pero es de sensor de alarma, es decir no se registra su valor continuamente por lo que no se puede decir su estado por la tabla de lectura
                pass
    
    database.put_conn(conn)
