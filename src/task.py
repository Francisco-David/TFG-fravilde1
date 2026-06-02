from pyzeebe import ZeebeTaskRouter, Job
import database

router = ZeebeTaskRouter()


@router.task(task_type="leerLecturas")
async def leer_lecturas(job: Job):
    sesion_id = job.variables.get("sesion_id")
    conn = database.get_conn()
    ultimas_lecturas = database.find_ultima_lectura_por_sensor(conn, sesion_id)
    sensors = database.find_todos_los_sensores(conn)
    for sensor in sensors:
        print(f'[CAMUNDA] TEST sensor: {sensor[0]}')
    conn.close()

    es_valida = True
    print(f'[CAMUNDA] TEST sesion_id: {sesion_id}, es_valida: {es_valida}')
    return {'esValida': es_valida}

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