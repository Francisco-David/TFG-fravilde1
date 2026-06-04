from pyzeebe import ZeebeTaskRouter, Job
import database
from datetime import datetime,timedelta

router = ZeebeTaskRouter()


@router.task(task_type="leerLecturas")
async def leer_lecturas(job: Job):
    res = {}
    sesion_id = job.variables.get("sesion_id")
    now = datetime.now()

    conn = database.get_conn()
    ultimas_lecturas = database.find_ultima_lectura_por_sensor(conn, sesion_id)
    sensors = database.find_todos_los_sensores(conn)
    database.put_conn(conn)
    
    dicc_lecturas = {lectura[0]: lectura for lectura in ultimas_lecturas}  # Creamos un diccionario para acceder a las lecturas por sensor_id
    for sensor in sensors:
        tipo_sensor = sensor[1]
        if tipo_sensor in ["mixto", "ambiental"]:
            nombre_sensor = sensor[0]
            validez = sensor[2]
            lectura_sensor = dicc_lecturas[nombre_sensor]

            res[f"{nombre_sensor}Valor"] = lectura_sensor[1]
            res[f"{nombre_sensor}Validez"] = (lectura_sensor[2]+timedelta(seconds=validez))>now # Chequeamos que la lectura no sea demasiado antigua sumando el valor de validez del sensor a su timestamp

    son_validas = all(res[f"{sensor[0]}Validez"] for sensor in sensors if sensor[1] in ["mixto", "ambiental"])
    res["sonValidas"] = son_validas
    
    print(f'[CAMUNDA] "leerLecturas" - sesion_id: {sesion_id}, sonValidas: {son_validas}\n (lecturas: {res})')
    return res

@router.task(task_type="calculoEvaluacion")
async def calcular_evaluacion(job: Job):
    sesion_id = job.variables.get("sesion_id")
    puntuacion = 80  # Aquí iría la lógica real para calcular la puntuación basada en las lecturas y otros factores

    conn = database.get_conn()
    database.insert_evaluacion(conn, sesion_id, puntuacion)
    database.put_conn(conn)
    
    print(f'[CAMUNDA] "calculoEvaluacion" - sesion_id: {sesion_id}, puntuacion: {puntuacion}')
    return {'puntuacion': puntuacion}

@router.task(task_type="comprobarEstado")
async def comprobar_estado(job: Job):
    sesion_id = job.variables.get("sesion_id")

    conn = database.get_conn()
    estado_sesion = database.find_estado_sesion(conn, sesion_id)
    database.put_conn(conn)

    print(f'[CAMUNDA] "comprobarEstado" - sesion_id: {sesion_id}, estado: {estado_sesion}')
    return {'estadoSesion': estado_sesion}

# @router.task(task_type="activateCooling")
# async def activate_cooling_task():
#     print("ACTIVATE COOLING TASK CALLED")
#     return {}


# @router.task(task_type="activateHeating")
# async def activate_heating_task():
#     print("ACTIVATE HEATING TASK CALLED")
#     return {}