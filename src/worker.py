import asyncio
import pyzeebe
from pyzeebe import ZeebeWorker, create_insecure_channel
from task import router
import database
import logging
import os

LOGS_DIR = "I:/UNIVERSIDAD/TFG/TFG-fravilde1/logs"

logger = logging.getLogger(__name__)

# WARNING de falta de jobs para activar cuando por ejemplo no hay jobs que hacer porque todos los sensores están operativos
# logging.getLogger("pyzeebe").setLevel(logging.ERROR)
logging.getLogger("grpc._cython.cygrpc").setLevel(logging.ERROR)
logging.getLogger("pyzeebe.worker.job_executor").setLevel(logging.ERROR)
logging.getLogger("pyzeebe.grpc_internals.zeebe_job_adapter").setLevel(logging.ERROR)

print("hello"+pyzeebe.__name__)

async def main():
    # CONFIGURAR LOGGING
    if not os.path.exists(LOGS_DIR):
        os.makedirs(LOGS_DIR)
    
    log_file = f"{LOGS_DIR}/worker.log"
    
    logging.basicConfig(
        level=logging.DEBUG,
        # format='%(asctime)s + %(name)s + [%(levelname)-s] %(message)s',
        format='%(asctime)s [%(levelname)-s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    

    channel = create_insecure_channel(grpc_address="localhost:26500")

    worker = ZeebeWorker(channel)
    worker.include_router(router)

    try:
        logger.info("[WORKER] Iniciando worker y esperando jobs...")
        await worker.work()
    except Exception as e:
        logger.error(f"[WORKER] {e}")

if __name__ == "__main__":
    try:
        database.init_pool()    
        asyncio.run(main())
    except KeyboardInterrupt:
        database.close_all()
        logger.info("[WORKER] Apagado completo.")