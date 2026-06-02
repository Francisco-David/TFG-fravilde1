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
    
    for sensor in sensors:
        nombre_sensor = sensor[0]
        validez = sensor[2]
        tipo_sensor = sensor[1]
        for lectura in ultimas_lecturas:
            if tipo_sensor in ["mixto", "ambiental"]:
                res[f"{nombre_sensor}Valor"] = lectura[1]
                res[f"{nombre_sensor}Validez"] = (lectura[2]+timedelta(seconds=validez))>now # Chequeamos que la lectura no sea demasiado antigua sumando el valor de validez del sensor a su timestamp
    
    son_validas = all(res[f"{nombre_sensor[0]}Validez"] for nombre_sensor in sensors if nombre_sensor[1] in ["mixto", "ambiental"]) 
    res["sonValidas"] = son_validas
    print(f'[CAMUNDA] TEST sesion_id: {sesion_id}, sonValidas: {son_validas} (lecturas: {res})')
    return res

@router.task(task_type="calculoEvaluacion")
async def calcular_evaluacion():
    puntuacion = 80
    print(f'[CAMUNDA] TEST calculo evaluacion: {puntuacion}')
    return {'puntuacion': puntuacion}

@router.task(task_type="comprobarEstado")
async def comprobar_estado():
    estadoSesion = "finalizada"
    print(f'[CAMUNDA] TEST comprobar estado: {estadoSesion}')
    return {'estadoSesion': estadoSesion}

# @router.task(task_type="activateCooling")
# async def activate_cooling_task():
#     print("ACTIVATE COOLING TASK CALLED")
#     return {}


# @router.task(task_type="activateHeating")
# async def activate_heating_task():
#     print("ACTIVATE HEATING TASK CALLED")
#     return {}