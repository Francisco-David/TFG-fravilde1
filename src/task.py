from pyzeebe import ZeebeTaskRouter, Job
import database
from datetime import datetime,timedelta
import logging
import alarm

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
        nombre_sensor = sensor[0]
        if estado_sensor=="operativo":
            lectura_sensor = dicc_lecturas[nombre_sensor]
            res[f"{nombre_sensor}Valor"] = lectura_sensor[1]
        elif estado_sensor=="defectuoso":
            res[f"{nombre_sensor}Valor"] = None

    
    logger.info(f'[CAMUNDA] "leerLecturas" - sesion_id: {sesion_id}\n (lecturas: {res})')
    return res

@router.task(task_type="calculoEvaluacion")
async def calcular_evaluacion(job: Job):
    sesion_id = job.variables.get("sesion_id")

    # def score_final(st, sh, ss, sl, ok_t, ok_h, ok_s, ok_l):
    scores = []
    pesos = []

    tem_valor = job.variables.get("temValor")
    hum_valor = job.variables.get("humValor")
    son_valor = job.variables.get("sonValor")
    luz_valor = job.variables.get("luzValor")

    if tem_valor is not None:
        tem_valor = 100
        if tem_valor < alarm.UMBRAL_ALARMA_TEM_MIN or tem_valor > alarm.UMBRAL_ALARMA_TEM_MAX:
            tem_valor =  0
        if tem_valor < alarm.UMBRAL_AVISO_TEM_MIN:
            tem_valor =  20
        if tem_valor > alarm.UMBRAL_AVISO_TEM_MAX:
            tem_valor =  40
        scores.append(tem_valor)
        pesos.append(0.3)

    if hum_valor is not None:
        hum_valor = 100

        if hum_valor > alarm.UMBRAL_ALARMA_HUM_MAX:
            hum_valor = 0
        elif hum_valor > alarm.UMBRAL_AVISO_HUM_MAX:
            hum_valor = 40

        scores.append(hum_valor)
        pesos.append(0.2)

    if son_valor is not None:
        son_valor = 100

        if son_valor > alarm.UMBRAL_ALARMA_SON_MAX:
            son_valor = 0
        elif son_valor > alarm.UMBRAL_AVISO_SON_MAX:
            son_valor = 40

        scores.append(son_valor)
        pesos.append(0.3)

    if luz_valor is not None:
        luz_valor = 100

        if luz_valor < alarm.UMBRAL_ALARMA_LUZ_MIN:
            luz_valor = 0
        elif luz_valor < alarm.UMBRAL_AVISO_LUZ_MIN:
            luz_valor = 40

        scores.append(luz_valor)
        pesos.append(0.2)

    conn = database.get_conn()

    if len(scores) == 0:
        puntuacion = 0
        nivel='AVISO'
        codigo = f'{nivel[:2]}allC'
        texto_aviso = f"[{nivel}] [CAMUNDA] Revise la conexión MQTT o la conexión a los sensores, todos carecen de valor."
        alarm.generar_alerta(conn, codigo, sesion_id, None, texto_aviso, nivel)
    else:
        puntuacion = round(sum(s * p for s, p in zip(scores, pesos)) / sum(pesos), 2)

    database.insert_evaluacion(conn, sesion_id, puntuacion)
    database.put_conn(conn)

    logger.info(f'[CAMUNDA] "calculoEvaluacion" - sesion_id: {sesion_id}, puntuacion: {puntuacion}')

    if puntuacion < (100/3):
        nivel='ALARMA'
        codigo = f'{nivel[:2]}allC'
        texto_aviso = f"[{nivel}] [CAMUNDA] La puntuación ambiental es CRÍTICA (score: {puntuacion}). Revise las condiciones de la clase INMEDIATAMENTE."
        alarm.generar_alerta(conn, codigo, sesion_id, None, texto_aviso, nivel)

    if puntuacion < (200/3):
        nivel='AVISO'
        codigo = f'{nivel[:2]}allC'
        texto_aviso = f"[{nivel}] [CAMUNDA] La puntuación ambiental comienza a deteriorarse (score: {puntuacion}). Revise las condiciones de la clase."
        alarm.generar_alerta(conn, codigo, sesion_id, None, texto_aviso, nivel)


    

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
                    nivel='INFO'
                    codigo = f'{nivel[:2]}{nombre_sensor}C'
                    texto_aviso = f"[{nivel}] [CAMUNDA] Se ha recuperado la conexión con el sensor {nombre_sensor}"
                    alarm.generar_alerta(conn, codigo, sesion_id, nombre_sensor, texto_aviso, nivel)
                    
                elif not validez_transmision and estado_sensor=='operativo':

                    database.update_estado_sensor(conn, nombre_sensor,'defectuoso')
                    # COMPROBAR SI HAY ALARMA ACK
                    #   SI NO HAY ALARMA O LA QUE HAY NO ESTÁ ACK METER AVISO "SE HA PERDIDO LA CONEXION"
                    nivel='AVISO'
                    codigo = f'{nivel[:2]}{nombre_sensor}C'
                    texto_aviso = f"[{nivel}] [CAMUNDA] Revise la conexión MQTT o la conexión física al sensor {nombre_sensor}"
                    alarm.generar_alerta(conn, codigo, sesion_id, nombre_sensor, texto_aviso, nivel)

            else: # Se ha recibido una lectura pero es de sensor de alarma, es decir no se registra su valor continuamente por lo que no se puede decir su estado por la tabla de lectura
                pass
    
    database.put_conn(conn)
