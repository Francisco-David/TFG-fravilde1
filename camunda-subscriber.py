import json
import paho.mqtt.client as mqtt
from pyzeebe import ZeebeClient, create_insecure_channel
import asyncio
import threading

# Config
PROCESS_ID = "temp-process"
ZEEBE_ADDRESS = "localhost:26500"
BROKER_ADDRESS = "10.245.208.86"
MQTT_PORT = 1883
MQTT_TOPIC = "tfg/sensors/temp"

# Background asyncio loop setup
def start_asyncio_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

async_loop = asyncio.new_event_loop()
loop_thread = threading.Thread(target=start_asyncio_loop, args=(async_loop,))
loop_thread.daemon = True
loop_thread.start()


# MQTT Callback
def on_message(client, userdata, msg):
    print(f"Received on {msg.topic}: {msg.payload.decode()}")
    try:
        payload = json.loads(msg.payload.decode())
        variables = {"temperature": payload.get("value")}

        future = asyncio.run_coroutine_threadsafe(
            start_camunda_process(variables), async_loop
        )
        # Callback to see exceptions from the async task
        future.add_done_callback(lambda f: f.result() if f.exception() is None else print(f"Async task failed: {f.exception()}"))

    except Exception as e:
        print(f"Error handling message: {e}")

# Async function to start camunda (via Zeebe) process. Create BOTH the channel and the client INSIDE the coroutine.
async def start_camunda_process(variables):
    try:
        channel = create_insecure_channel(grpc_address=ZEEBE_ADDRESS)
        zeebe_client = ZeebeClient(channel)
        
        print(f"Starting process '{PROCESS_ID}' with variables: {variables}")
        await zeebe_client.run_process(PROCESS_ID, variables)
        print("Process started successfully.")
    except Exception as e:
        print(f"Error starting Camunda process: {e}")


# MQTT Config
mqtt_client = mqtt.Client()
mqtt_client.on_message = on_message
mqtt_client.connect(BROKER_ADDRESS, MQTT_PORT, 60)
mqtt_client.subscribe(MQTT_TOPIC)

print(f"Subscribed to topic '{MQTT_TOPIC}'. Waiting for messages...")
try:
    mqtt_client.loop_forever()
except KeyboardInterrupt:
    print("\nShutting down...")
finally:
    mqtt_client.disconnect()
    if async_loop.is_running():
        async_loop.call_soon_threadsafe(async_loop.stop)
    print("Shutdown complete.")