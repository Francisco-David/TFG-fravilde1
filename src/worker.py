import asyncio
from pyzeebe import ZeebeWorker, create_insecure_channel
from task import router
import database
import logging

# WARNING de falta de jobs para activar cuando por ejemplo no hay jobs que hacer porque todos los sensores están operativos
logging.getLogger("pyzeebe").setLevel(logging.ERROR)

async def main():
    channel = create_insecure_channel(grpc_address="localhost:26500")

    worker = ZeebeWorker(channel)
    worker.include_router(router)

    try:
        print("[WORKER] Iniciando worker y esperando jobs...")
        await worker.work()
    except Exception as e:
        print(f"[WORKER] ERROR: {e}")

if __name__ == "__main__":
    try:
        database.init_pool()    
        asyncio.run(main())
    except KeyboardInterrupt:
        database.close_all()
        print("[WORKER] Apagado completo.")