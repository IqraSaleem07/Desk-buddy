# Desk Buddy

A small desk companion built on an ESP32-C3 that shows the time, date,
live weather, and a face whose mood follows the weather. One touch
sensor cycles through five screens. It's written in MicroPython and was
built as a hands-on way to learn embedded basics: GPIO, I2C, WiFi, NTP,
HTTP APIs, and non-blocking program structure.

## Demo

[**Watch the demo (media/demo.mp4)**](media/demo.mp4)

A 24-second clip of the build running on a breadboard. One tap at a
time it steps through the screens: the face, the big clock, the weekday
and date, the WiFi info screen (blurred to hide the network name), the
weather screen with the sun icon and temperature, and back to the face.

> Tip: for an inline video player on the repo page, open README.md in
> GitHub's editor and drag `demo.mp4` into it. GitHub then hosts it and
> embeds a player.

## Features

- **Big clock** synced over WiFi with NTP, shown in a large font
- **Weekday + date** screen
- **WiFi info** screen (network name and IP address)
- **Weather** screen from OpenWeatherMap, with a hand-drawn sun, cloud
  or rain icon and the temperature
- **Face** screen: smiles when it's clear, frowns when it's cloudy or
  rainy
- **One touch sensor** (TTP223) changes the screen, with one tap giving
  exactly one change
- A **non-blocking main loop**: the clock, the touch input and the
  10-minute weather refresh share one loop and never freeze each other

## Hardware

| Part | Notes | Approx. price (India) |
|---|---|---|
| ESP32-C3 SuperMini | Main board, runs MicroPython | ₹150–250 |
| 1.3" OLED, SH1106, I2C, 128x64 | Display (note: SH1106, not SSD1306) | ₹280–330 |
| TTP223 capacitive touch module | Switches screens | ₹15–40 |
| Jumper wires, breadboard, USB-C data cable | Prototyping and power | varies |
| Cardboard | Optional enclosure | – |

Prices are rough and change over time.

Why these parts:

- **TTP223 instead of a bare touch pad.** The original ESP32 has a
  built-in capacitive touch peripheral. The ESP32-C3 does not, so a
  small touch module that outputs a plain digital HIGH/LOW does the job.
- **SH1106 driver, not SSD1306.** Many 1.3" modules use the SH1106
  chip. The common `ssd1306.py` driver doesn't match it, so this repo
  ships `sh1106.py`.

Wiring and pin choices are in [WIRING.md](WIRING.md).

## Quick start

1. **Flash MicroPython** onto the board. Download the `.bin` for
   `ESP32_GENERIC_C3` from micropython.org (not the `.app-bin`), then
   put the board in bootloader mode (hold BOOT, tap RST, release BOOT)
   and run:
   ```
   python -m esptool --chip esp32c3 --port COMx erase-flash
   python -m esptool --chip esp32c3 --port COMx --baud 460800 write-flash -z 0x0 ESP32_GENERIC_C3-<version>.bin
   ```
   Put the board back in bootloader mode between the two commands,
   because it resets itself after the erase. Older esptool versions use
   `erase_flash` and `write_flash` with underscores.
2. **Install [Thonny](https://thonny.org)**, set the interpreter to
   MicroPython (ESP32), and pick the board's COM port.
3. **Copy `sh1106.py` onto the board** (File → Save as → MicroPython
   device). `import sh1106` runs on the board, so the file has to live
   in the board's own storage.
4. **Add your credentials.** Edit the constants at the top of
   `desk_buddy.py` (WiFi name, password, OpenWeatherMap API key, city),
   or copy `secrets_example.py` to `secrets.py`, fill it in, and import
   from it. `secrets.py` is git-ignored.
5. **Test the hardware** with the scripts in [`tests/`](tests/) (LED
   blink, I2C scan, touch sensor) before running the full program.
6. **Run `desk_buddy.py`** from Thonny. To make it start on power-up,
   save it to the board as `main.py`.

## How it works

The code is organised around one rule: **never block the main loop.**

- **One loop, three timers.** The main `while True:` loop checks the
  touch pin on every pass, redraws once per second, and refetches the
  weather every 10 minutes. Each timer uses `time.ticks_ms()` and
  `time.ticks_diff()`. Calling `time.sleep(1)` instead would freeze the
  touch check for a full second at a time, so a tap could be missed.
  `ticks_diff()` is used because the tick counter wraps around, and
  plain subtraction breaks at the wrap.
- **One tap, one change.** The code watches for the touch pin going
  from 0 to 1 (a rising edge), not for the pin being 1. Holding your
  finger down would otherwise register as dozens of taps. A 250 ms
  debounce covers contact chatter.
- **Pull-down on the touch pin.** `Pin.PULL_DOWN` gives the input a
  defined 0 when the sensor isn't driving it. Without it the pin
  floats and reads random values.
- **Screen state machine.** A single `screen_index` decides what
  `draw()` renders. The touch handler only changes the index and calls
  `draw()` straight away, so the screen changes immediately instead of
  waiting for the next 1-second tick.
- **Big text.** The built-in font is a fixed 8x8, so `big_text()`
  renders the string into a small off-screen `framebuf`, then stamps
  each lit pixel as a `scale x scale` block on the display.
- **Time.** `ntptime.settime()` sets the board's clock to UTC. The
  script adds an offset (19800 s for India, UTC+5:30) when it reads the
  time. The clock keeps counting between syncs, but the board forgets
  the time if it loses power, so it needs WiFi again at every boot.
- **Weather.** `urequests` calls the OpenWeatherMap current-weather
  endpoint with `units=metric`. The condition text (`Clear`, `Clouds`,
  `Rain`) picks the icon and the face's mood.
- **Software I2C.** `SoftI2C` lets you choose any two GPIO pins for the
  OLED instead of being tied to fixed hardware I2C pins.

## Project layout

```
desk-buddy/
├── desk_buddy.py        main program
├── sh1106.py            SH1106 OLED driver (third party, MIT, see Credits)
├── secrets_example.py   template for credentials
├── media/
│   └── demo.mp4         demo video of the screens cycling
├── tests/               small hardware tests, one per part
│   ├── led_blink.py
│   ├── wifi_scan.py
│   ├── i2c_scan.py
│   └── touch_test.py
├── WIRING.md            pin map and wiring notes
├── TROUBLESHOOTING.md   problems hit while building, with fixes
├── LICENSE
└── README.md
```

## Assembly and soldering notes

- **Prototype on a breadboard first.** Confirm each part with its test
  script, then solder.
- **The touch module needs all three pins connected.** The signal pin
  and VCC alone are not enough, because without GND the module has no
  return path and reads unreliably.
- **Check every connection after soldering.** A joint that looks
  connected can still be a cold joint. Give each wire a gentle tug, and
  re-run the part's test script afterwards.
- **If solder balls up instead of sticking:**
  - Heat the pad and the pin together for a second or two, then feed
    solder into that joint, not onto the iron tip.
  - Keep the tip clean and shiny, and wipe it and re-tin it often.
  - Use proper electronics solder (a tin alloy with flux in the core),
    not aluminium wire. Aluminium forms an oxide layer that ordinary
    solder won't bond to.
  - Dull, tarnished pads and pins may need a little extra flux.
  - Around 300–350 °C works for most hobby joints.
- **Power safety.** Connect the OLED's VCC to the **3.3 V** pin, never
  5 V, and double-check VCC and GND are not swapped before powering on.
  On the SuperMini the ground pin is the one labelled **G**.

## Build log

How it was built, in order, up to the first time everything worked
together.

1. **Chose the parts.** ESP32-C3 SuperMini for the small size and
   WiFi. A TTP223 touch module for input, since the C3 has no touch
   peripheral. A 1.3" SH1106 OLED for the display.
2. **Prototyped the weather call in desktop Python first.** A PC needs
   no hardware, so it's a fast way to get the API call, the JSON
   parsing and the error handling right. The first versions hit a
   missing `s` in `requests`, missing quotes around the URL, an f-string
   with spaces in the placeholder names, indentation errors, and a
   `utcfromtimestamp` typo. The OpenWeatherMap docs example used `lat`
   and `lon`, but city-name lookup uses `q=`.
3. **Practised non-blocking timing** by replacing `time.sleep()` with
   `ticks_ms()` and `ticks_diff()`, first on an LED blink.
4. **Flashed MicroPython with `esptool`.** Thonny's built-in installer
   failed with `invalid header: 0xffffffff` on a blank chip. A manual
   erase and flash in bootloader mode fixed it. See
   [TROUBLESHOOTING.md](TROUBLESHOOTING.md).
5. **Blinked the onboard LED** (GPIO 8) to confirm the toolchain end to
   end.
6. **Got WiFi working** by scanning, connecting at the REPL, and then
   wrapping it in a function.
7. **Added NTP time sync** with the India offset, then hardened WiFi
   with a timeout, retries, a radio reset and lower TX power after
   intermittent connection failures.
8. **Wired the OLED**, confirmed it with an I2C scan (`[60]`), saved the
   SH1106 driver on the board, and showed a live clock on it.
9. **Added the touch sensor.** The reading floated until `PULL_DOWN` was
   added, GPIO 4 read unreliably so the sensor moved to GPIO 3, and a
   loose wire briefly made it look broken.
10. **Combined everything** into one script with a `draw()` function
    switching on `screen_index`, with an immediate redraw on touch and a
    debounce.
11. **Added big text, the weather screen with icons, and the face.**
    The SH1106 driver's `ellipse()` takes only five arguments, so the
    icons are outlines. The face's smile and frown were inverted at
    first and needed the formulas swapped.
12. **First full run:** WiFi, NTP, weather, touch cycling and all five
    screens working together.

## Credits

`sh1106.py` is third-party code by Radomir Dopieralski, Robert
Hammelrath ([robert-hh](https://github.com/robert-hh/SH1106)) and Tim
Weber, used under the MIT License. The copyright notice at the top of
that file must stay with it.

Weather data is from [OpenWeatherMap](https://openweathermap.org).

## License

MIT, see [LICENSE](LICENSE). This covers the original code in this
repo. `sh1106.py` carries its own copyright notice, as above.
