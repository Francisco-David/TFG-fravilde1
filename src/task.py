from pyzeebe import ZeebeTaskRouter, Job

router = ZeebeTaskRouter()


@router.task(task_type="leerLecturas")
async def leer_lecturas(job: Job):
    sesion_id = job.variables.get("sesion_id")
    
    pass
    return {}


# @router.task(task_type="activateCooling")
# async def activate_cooling_task():
#     print("ACTIVATE COOLING TASK CALLED")
#     return {}


# @router.task(task_type="activateHeating")
# async def activate_heating_task():
#     print("ACTIVATE HEATING TASK CALLED")
#     return {}