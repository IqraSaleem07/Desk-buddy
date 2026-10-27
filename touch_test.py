# Prints 0 when untouched and 1 while the pad is touched.
# The pull-down gives the pin a clean 0 when nothing drives it.
from machine import Pin
import time

TOUCH_PIN = 3

touch = Pin(TOUCH_PIN, Pin.IN, Pin.PULL_DOWN)

while True:
    print(touch.value())
    time.sleep_ms(200)
