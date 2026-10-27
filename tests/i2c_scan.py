# A working SH1106 OLED shows up as [60] (0x3c).
from machine import Pin, SoftI2C

SDA_PIN = 5
SCL_PIN = 6

i2c = SoftI2C(sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=400000)
print(i2c.scan())
