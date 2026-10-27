# Wiring

Board: **ESP32-C3 SuperMini**

| Component | Component pin | ESP32-C3 pin |
|---|---|---|
| OLED (1.3" SH1106, I2C) | VCC | 3.3 |
| OLED | GND | G |
| OLED | SDA | GPIO 5 |
| OLED | SCL | GPIO 6 |
| Touch sensor (TTP223) | VCC | 3.3 |
| Touch sensor | GND | G |
| Touch sensor | I/O (OUT/SIG) | GPIO 3 |

The pins on one edge of the SuperMini read `5V, G, 3.3, 4, 3, 2, 1, 0`
and the other edge reads `5, 6, 7, 8, 9, 10, 20, 21`. Go by the
silkscreen labels on your board, since the layout can differ slightly
between sellers.

## Notes

- **Power.** Use the `3.3` pin for both VCC wires, never `5V`. The
  OLED and the touch module can share the `3.3` pin and the `G` pin,
  for example through a breadboard rail.
- **Ground.** `G` is the ground pin, next to `5V`.
- **Pins to avoid for other uses.** GPIO 8 drives the onboard LED and
  GPIO 9 is the BOOT button, so keep both free.
- **Touch pin.** GPIO 4 was tried first and read unreliably. GPIO 3
  with an internal pull-down (`Pin(3, Pin.IN, Pin.PULL_DOWN)`) is
  stable.
- **Changing pins.** Edit `SDA_PIN`, `SCL_PIN` and `TOUCH_PIN` near the
  top of `desk_buddy.py` so the code matches where the wires are.
- **The onboard LEDs.** The red one is just a power indicator. The blue
  one is the programmable LED on GPIO 8.

## Quick hardware tests

Run these at the MicroPython REPL, or use the scripts in `tests/`.
Type them one line at a time, with no leading spaces.

**OLED. Should return `[60]`:**
```python
from machine import Pin, SoftI2C
i2c = SoftI2C(sda=Pin(5), scl=Pin(6), freq=400000)
i2c.scan()
```

A working display answers at one address, `60` (`0x3c`).

**Touch sensor. Reads 0 untouched, 1 touched:**
```python
from machine import Pin
touch = Pin(3, Pin.IN, Pin.PULL_DOWN)
touch.value()
```

Most TTP223 modules also have a small LED that lights while you touch
the pad, which shows the module itself is working.

**LED. Should blink once a second:**
```python
from machine import Pin
import time
led = Pin(8, Pin.OUT)
while True:
    led.value(1)
    time.sleep(0.5)
    led.value(0)
    time.sleep(0.5)
```
