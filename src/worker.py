import asyncio
from pyzeebe import ZeebeWorker, create_insecure_channel
from task import router
import database


async def main():

    database.init_pool()  # Inicializamos la base de datos al iniciar el worker
    channel = create_insecure_channel(grpc_address="localhost:26500")


    worker = ZeebeWorker(channel)
    worker.include_router(router)
    await worker.work()


asyncio.run(main())
