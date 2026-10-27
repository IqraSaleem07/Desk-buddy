"""
Desk Buddy - ESP32-C3 SuperMini + 1.3" SH1106 OLED + TTP223 touch sensor

Screens (touch cycles through them):
  0 big clock   1 weekday + date   2 WiFi info   3 weather   4 face

Fill in SSID, PASSWORD, API_KEY and CITY before running.
sh1106.py must be saved on the board next to this file.
"""

import network
import ntptime
import time
import math
import framebuf
from machine import Pin, SoftI2C
import sh1106
import urequests

# ---- fill these in ----
SSID = 'YOUR_WIFI_NAME'
PASSWORD = 'YOUR_WIFI_PASSWORD'
API_KEY = 'YOUR_OPENWEATHERMAP_API_KEY'
CITY = 'Kanpur'
# -----------------------

IST_OFFSET = 19800                  # UTC+5:30 in seconds
WEATHER_EVERY_MS = 10 * 60 * 1000   # refresh weather every 10 minutes
NUM_SCREENS = 5

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday",
        "Friday", "Saturday", "Sunday"]

# ---- pins ----
SDA_PIN = 5
SCL_PIN = 6
TOUCH_PIN = 3

i2c = SoftI2C(sda=Pin(SDA_PIN), scl=Pin(SCL_PIN), freq=400000)
i2c.writeto(0x3c, bytes([0x00, 0xA4]))   # show RAM contents
i2c.writeto(0x3c, bytes([0x00, 0xA6]))   # normal (not inverted) display

oled = sh1106.SH1106_I2C(128, 64, i2c, None, 0x3c)
oled.sleep(False)

touch = Pin(TOUCH_PIN, Pin.IN, Pin.PULL_DOWN)
screen_index = 0
last_touch_state = 0
last_touch_time = 0

weather = None
weather_msg = "Loading..."


def big_text(s, x, y, scale=3):
    # The built-in font is a fixed 8x8, so draw the text into a tiny
    # off-screen buffer and stamp each lit pixel as a scale x scale block.
    w = 8 * len(s)
    buf = bytearray(w)
    fb = framebuf.FrameBuffer(buf, w, 8, framebuf.MONO_HLSB)
    fb.text(s, 0, 0, 1)
    for row in range(8):
        for col in range(w):
            if fb.pixel(col, row):
                oled.fill_rect(x + col * scale, y + row * scale, scale, scale, 1)


def draw_sun(cx, cy, r=10):
    oled.ellipse(cx, cy, r, r, 1)       # this driver's ellipse takes 5 args
    for angle in range(0, 360, 45):
        x1 = cx + int((r + 3) * math.cos(math.radians(angle)))
        y1 = cy + int((r + 3) * math.sin(math.radians(angle)))
        x2 = cx + int((r + 7) * math.cos(math.radians(angle)))
        y2 = cy + int((r + 7) * math.sin(math.radians(angle)))
        oled.line(x1, y1, x2, y2, 1)


def draw_cloud(cx, cy):
    oled.ellipse(cx - 10, cy, 8, 6, 1)
    oled.ellipse(cx, cy - 4, 10, 8, 1)
    oled.ellipse(cx + 10, cy, 8, 6, 1)
    oled.fill_rect(cx - 14, cy, 28, 8, 1)


def draw_weather_icon(condition, cx, cy):
    condition = condition.lower()
    if "rain" in condition:
        draw_cloud(cx, cy)
        for dx in (-10, 0, 10):
            oled.line(cx + dx, cy + 8, cx + dx - 2, cy + 14, 1)
    elif "cloud" in condition:
        draw_cloud(cx, cy)
    else:
        draw_sun(cx, cy)


def draw_face(mood="neutral"):
    oled.ellipse(40, 24, 10, 10, 1)
    oled.ellipse(88, 24, 10, 10, 1)
    oled.fill_rect(36, 20, 4, 4, 1)
    oled.fill_rect(84, 20, 4, 4, 1)
    if mood == "happy":
        for dx in range(-15, 16):
            y = 45 + int((15 * 15 - dx * dx) ** 0.5) // 4
            oled.pixel(64 + dx, y, 1)
    elif mood == "sad":
        for dx in range(-15, 16):
            y = 50 - int((15 * 15 - dx * dx) ** 0.5) // 4
            oled.pixel(64 + dx, y, 1)
    else:
        oled.hline(49, 48, 30, 1)


def do_connect(attempts=3, timeout_ms=20000):
    # Status codes: 201 network not found, 202 auth failed,
    # 1001 still connecting, 1010 got IP.
    wlan = network.WLAN(network.STA_IF)
    for attempt in range(attempts):
        print("connecting, attempt", attempt + 1)
        wlan.active(False)
        time.sleep_ms(500)
        wlan.active(True)
        wlan.config(txpower=8)          # lower TX power helps SuperMini boards
        wlan.disconnect()
        wlan.connect(SSID, PASSWORD)
        start = time.ticks_ms()
        while not wlan.isconnected():
            if time.ticks_diff(time.ticks_ms(), start) > timeout_ms:
                break
            time.sleep_ms(100)
        if wlan.isconnected():
            print('network config: ', wlan.ifconfig())
            return True
        print("attempt failed, status:", wlan.status())
    print("WiFi failed after", attempts, "attempts")
    return False


def sync_time():
    for attempt in range(5):
        try:
            ntptime.settime()
            print("time synced")
            return True
        except OSError:
            print("sync failed, retrying...")
            time.sleep(1)
    return False


def fetch_weather():
    global weather, weather_msg
    if not network.WLAN(network.STA_IF).isconnected():
        weather_msg = "No WiFi"
        return
    try:
        url = ("http://api.openweathermap.org/data/2.5/weather"
               "?q=%s&appid=%s&units=metric" % (CITY, API_KEY))
        r = urequests.get(url)
        d = r.json()
        r.close()
        if "main" in d:
            weather = {
                "temp": d["main"]["temp"],
                "desc": d["weather"][0]["main"],
            }
            print("weather:", weather)
        else:
            weather_msg = "API err " + str(d.get("cod"))
    except Exception as e:
        weather_msg = "Weather failed"
        print("weather failed:", e)


def draw():
    oled.fill(0)
    if screen_index == 0:
        t = time.localtime(time.time() + IST_OFFSET)
        big_text("%02d:%02d" % (t[3], t[4]), 0, 0, 3)
        oled.text("%02d/%02d/%d" % (t[2], t[1], t[0]), 0, 40, 1)
    elif screen_index == 1:
        t = time.localtime(time.time() + IST_OFFSET)
        big_text(DAYS[t[6]][:6], 0, 0, 2)
        big_text("%02d/%02d" % (t[2], t[1]), 0, 34, 2)
        oled.text(str(t[0]), 0, 54, 1)
    elif screen_index == 2:
        wlan = network.WLAN(network.STA_IF)
        if wlan.isconnected():
            oled.text("WiFi: " + SSID, 0, 0, 1)
            oled.text(wlan.ifconfig()[0], 0, 16, 1)
        else:
            oled.text("WiFi offline", 0, 0, 1)
    elif screen_index == 3:
        if weather:
            draw_weather_icon(weather["desc"], 30, 30)
            big_text("%dC" % round(weather["temp"]), 60, 20, 2)
            oled.text(weather["desc"], 0, 54, 1)
        else:
            oled.text(weather_msg, 0, 0, 1)
    else:
        if weather:
            desc = weather["desc"].lower()
            if "clear" in desc or "sun" in desc:
                draw_face("happy")
            elif "cloud" in desc or "rain" in desc:
                draw_face("sad")
            else:
                draw_face("neutral")
        else:
            draw_face("neutral")
    oled.show()


if do_connect():
    sync_time()
    fetch_weather()

interval = 1000
last_tick = time.ticks_ms()
last_weather = time.ticks_ms()
draw()

while True:
    current_touch = touch.value()
    now = time.ticks_ms()

    # rising edge (0 -> 1) plus a 250 ms debounce = one screen change per tap
    if (current_touch == 1 and last_touch_state == 0
            and time.ticks_diff(now, last_touch_time) > 250):
        last_touch_time = now
        screen_index = (screen_index + 1) % NUM_SCREENS
        print("screen_index:", screen_index)
        draw()
    last_touch_state = current_touch

    if time.ticks_diff(now, last_tick) >= interval:
        last_tick = now
        draw()

    if time.ticks_diff(now, last_weather) >= WEATHER_EVERY_MS:
        last_weather = now
        fetch_weather()

    time.sleep_ms(10)
