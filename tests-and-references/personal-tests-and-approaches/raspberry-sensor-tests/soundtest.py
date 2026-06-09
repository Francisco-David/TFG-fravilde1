import RPi.GPIO as GPIO
from time import sleep

# Set the Raspberry Pi GPIO pin number where the sound sensor is connected
SOUND_SENSOR_PIN = 7

# Set the GPIO mode and configure the sound sensor pin as INPUT
GPIO.setmode(GPIO.BCM)
GPIO.setup(SOUND_SENSOR_PIN, GPIO.IN)

# Initialize the previous state variable with the current state
prev_sound_state = GPIO.input(SOUND_SENSOR_PIN)

try:
    while True:
        # Read the current state of the sound sensor
        sound_state = GPIO.input(SOUND_SENSOR_PIN)
        print(sound_state)
        # Check for a state change (LOW to HIGH or HIGH to LOW)
        if sound_state != prev_sound_state:
            if sound_state == GPIO.LOW:
                print("Sound detected!")

        # Update the previous state variable
        prev_sound_state = sound_state

        # Add a small delay to prevent continuous readings
        sleep(0.1)

except KeyboardInterrupt:
    # Clean up GPIO settings when Ctrl+C is pressed
    GPIO.cleanup()
    print("\nExiting the program.")