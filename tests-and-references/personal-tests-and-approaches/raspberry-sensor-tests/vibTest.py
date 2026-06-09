from flask import Flask, render_template
# import RPi.GPIO as GPIO
import time
import threading

# Setup GPIO
PIR_PIN = 17  # Pin connected to PIR sensor
LED_PIN = 18  # Pin connected to LED or buzzer

# GPIO.setmode(GPIO.BCM)
# GPIO.setup(PIR_PIN, GPIO.IN)
# GPIO.setup(LED_PIN, GPIO.OUT)

# Flask app setup
app = Flask(__name__)

# Shared motion detection state
motion_state = {"detected": False}

# Function to monitor motion
def monitor_motion():
    while True:
#        if GPIO.input(PIR_PIN):  # Motion detected
        if True:  # Motion detected
            motion_state["detected"] = True
            # GPIO.output(LED_PIN, GPIO.HIGH)  # Turn on LED/Buzzer
            time.sleep(1)
        else:
            motion_state["detected"] = False
            GPIO.output(LED_PIN, GPIO.LOW)  # Turn off LED/Buzzer
        time.sleep(0.1)

# Flask route
@app.route("/")
def index():
    return render_template("motion.html", motion=motion_state["detected"])

# Start motion monitoring thread
motion_thread = threading.Thread(target=monitor_motion, daemon=True)
motion_thread.start()

# Run Flask app
if __name__ == "__main__":
    try:
        app.run(host="0.0.0.0", port=5000)
    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        # GPIO.cleanup()
        print("Finally")
