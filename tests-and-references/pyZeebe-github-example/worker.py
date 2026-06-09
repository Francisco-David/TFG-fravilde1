import asyncio
from pyzeebe import ZeebeWorker, Job, create_camunda_cloud_channel, create_insecure_channel
from dotenv import load_dotenv
import os
from task import router


async def main():

    channel = create_insecure_channel(grpc_address="localhost:26500")

    worker = ZeebeWorker(channel)
    worker.include_router(router)
    await worker.work()


asyncio.run(main())
