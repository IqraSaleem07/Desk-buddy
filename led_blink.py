# Confirms the board runs MicroPython and GPIO works.
# The programmable (blue) LED on the SuperMini is on GPIO 8.
from machine import Pin
import time

led = Pin(8, Pin.OUT)

while True:
    led.value(1)
    time.sleep(0.5)
    led.value(0)
    time.sleep(0.5)
