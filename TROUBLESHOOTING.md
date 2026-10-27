# Troubleshooting

Problems hit while building this, grouped by area, each with the symptom,
the cause and the fix. When something fails, test one part at a time
with the scripts in `tests/` before running the full program.

## Flashing MicroPython

**Thonny prints `invalid header: 0xffffffff` many times, then
`Write timeout`.**
The chip's flash is blank, so there is no MicroPython for Thonny to talk
to. Thonny can't fix this. Flash the firmware with `esptool`:

```
python -m esptool --chip esp32c3 --port COMx erase-flash
python -m esptool --chip esp32c3 --port COMx --baud 460800 write-flash -z 0x0 ESP32_GENERIC_C3-<version>.bin
```

- Get the `.bin` for `ESP32_GENERIC_C3` from micropython.org. Use the
  plain `.bin`, not `.app-bin`, `.elf` or `.map`.
- Find `COMx` in Device Manager under Ports (COM & LPT).
- Close Thonny first so it isn't holding the port.
- Newer esptool versions print a warning that `erase_flash` and
  `write_flash` are deprecated in favour of `erase-flash` and
  `write-flash`. The old names still work.

**esptool can't connect.**
Put the board into bootloader mode: hold **BOOT**, tap **RST**, then
release BOOT. The board resets itself after the erase, so repeat this
before the flash command. Also try a different USB cable (some are
power-only) or a different USB port.

**A "choose an app to open this .bin file" dialog appears.**
You double-clicked the firmware. A `.bin` isn't meant to be opened. It is
flashed with the `esptool` command above.

**`Device is busy or does not respond` after flashing.**
Close the terminal that ran esptool, since it can still hold the port.
Then press **RST** on its own (no BOOT held) so the board runs the new
firmware instead of staying in download mode, and click
Stop/Restart in Thonny. Check the interpreter says MicroPython (ESP32)
and the right port.

**Connected, but it's not clear it's alive.**
The banner `MicroPython v... ESP32C3 module` and a `>>>` prompt mean
it is. Then run `print("hello")`.

## Thonny and the REPL

**`IndentationError: unexpected indent` at the `>>>` prompt.**
You pasted lines with leading spaces, or copied a `>>>` along with the
code. Type each line by hand with no leading spaces. For anything with
loops or functions, put it in the editor tab and press F5.

**`SyntaxError` after running a script while it was waiting for input.**
Press Run once and wait for the prompt before typing. Running again
while it waits sends the prompt text to the REPL as code.

**`NameError: name 'i2c' isn't defined` (or `oled`, `wlan`).**
Variables you create at the REPL are lost whenever the board restarts,
including after Stop/Restart. Retype the setup lines, or run a script
that creates them at the top.

**A script I named `time.py` breaks `import time`.**
Your file shadows the real module. Name scripts something else.

**Thonny shows `Write timeout` or the connection drops after pressing
Stop during a network call.**
Interrupting the board in the middle of a WiFi or NTP request can leave
the serial link in a bad state. Unplug and replug the board and
reconnect.

**The screen froze on one frame.**
The script crashed and stopped, so the display keeps its last frame.
Read the traceback in the Shell.

## LED

- The red LED is a power indicator and doesn't blink from code. The blue
  one is on GPIO 8.
- On some boards the LED is active-low, so `value(0)` turns it on.

## Timing and the main loop

- `time.sleep()` inside the main loop freezes everything else (touch,
  redraw, weather) for that long. Use `ticks_ms()` with `ticks_diff()`.
- Use `ticks_diff(now, then)`, not `now - then`, because the tick counter
  wraps around.
- Having two `while True:` loops in one file means the second never runs.

## WiFi

**Read the status code.** Print `wlan.status()` when a connection fails.

| Code | Meaning | What to try |
|---|---|---|
| 201 | Network not found | Is the hotspot or router on? Is it **2.4 GHz**? Run `wlan.scan()` and look for it |
| 202 | Authentication failed | Check the password. See the false-alarm note below |
| 1001 | Still connecting | Wait, retry, or unplug and replug the board |
| 1010 | Got an IP | Connected |

**Always 201, but it worked before.**
The ESP32-C3 only supports 2.4 GHz. A phone hotspot may have switched to
5 GHz, shut itself off after a period with no devices, or changed its
name. Check the hotspot, then run `wlan.scan()` to see what the board
can see.

**202, but the password is correct.**
This was a false alarm. The same credentials worked when typed at the
REPL. After a soft reboot the radio can be left in a half-finished
state. Resetting it before each attempt fixed it: `active(False)`, a
short sleep, `active(True)`.

**Stuck on "connecting" forever.**
A bare `while not wlan.isconnected(): pass` never ends if the connection
fails. Add a timeout using `ticks_diff` and print the status code when
it expires.

**Intermittent failures on the SuperMini.**
These boards connect unreliably at full transmit power for some people.
`wlan.config(txpower=8)` before connecting helped, along with retrying
up to three times.

**Still stuck.**
A full unplug and replug clears the radio more reliably than Thonny's
Stop/Restart.

## Time (NTP)

**The clock shows the right time but "time synced" never printed.**
After a soft reboot the board keeps its old clock, so a stale time can
look correct even though the sync failed. After a full power loss it
falls back to the year 2000. Trust the `time synced` line, not just the
clock.

**Time is off by hours.**
`ntptime.settime()` sets the clock to UTC. Add your offset in seconds
(India: 19800, which is 5 h 30 min).

**`OSError: [Errno 116] ETIMEDOUT` during sync.**
NTP uses UDP and an occasional packet gets dropped. Retry a few times,
as `sync_time()` does.

**Time drifts after many hours.**
The internal clock isn't perfect. Re-run `sync_time()` occasionally.

**MicroPython dates start at 2000, not 1970.**
Timestamps from MicroPython and desktop Python differ by that offset.

## Weather API

**Screen shows `API err 401`.**
A new OpenWeatherMap key can take a while to activate, sometimes up to a
couple of hours. Try again later.

**City not found, or wrong place.**
The docs example uses `lat` and `lon`. For a city name use `q=City` (add
`,IN` to narrow it down). Don't leave `{lat}` or `{lon}` placeholders in
the URL.

**Temperatures look like 300.**
They're in kelvin. Add `units=metric` to the URL for Celsius.

**I wanted a daily forecast but only get one reading.**
The `/data/2.5/weather` endpoint returns a current snapshot. The free
`/data/2.5/forecast` endpoint returns 3-hour steps for 5 days, as a
list you filter yourself.

**`ImportError: no module named 'requests'` on the board.**
MicroPython uses `urequests`. On a PC use `requests`.

**Keep your API key out of git.** Use `secrets.py` (git-ignored).

## Touch sensor

**The pin reads random values or sticks at 1.**
A floating input. Enable the internal pull-down:
`Pin(3, Pin.IN, Pin.PULL_DOWN)`.

**The value never changes when touched.**
- The module needs **VCC, GND and the signal pin** all connected. An
  unsoldered GND won't work.
- Most TTP223 boards have an LED that lights while touched. If it does,
  the module is fine and the problem is the wire to the GPIO.
- A loose jumper or poor solder joint made it look dead at first.
  Reseat the wires and re-solder if needed.
- GPIO 4 read unreliably here. Moving the signal wire to GPIO 3 worked.

**One tap changes the screen several times.**
React to the rising edge (0 then 1), not to the pin being 1, and add a
debounce interval (250 ms here).

**Nothing happens with a touch sensor on the ESP32-C3's touch pins.**
The C3 has no capacitive touch peripheral, so use the TTP223 module's
digital output instead.

## OLED and drawing

**`i2c.scan()` returns `[]`.**
Nothing is answering. Check the four wires, that SDA and SCL aren't
swapped, and that the pins in the code match where the wires are.

**Garbled or shifted text.**
The module is probably not what the seller says. Try the other driver,
SH1106 versus SSD1306. The SH1106 has 132 columns of internal RAM for a
128-pixel screen, which the driver handles with a 2-column offset.

**Text appears only after `oled.show()`.**
`fill()` and `text()` change a memory buffer. `show()` sends it to the
screen.

**`TypeError: function takes 7 positional arguments but 8 were given`
in `draw_sun`.**
This driver's `ellipse(x, y, xr, yr, color)` takes five arguments with no
"filled" flag, unlike standard `framebuf`. Remove the extra argument.
Ellipses are outlines only, so the icons are outlines, and a filled area
can be built with `fill_rect()`.

**Big text runs off the edge.**
Each character is `8 * scale` pixels wide on a 128-pixel screen. Reduce
the scale or shorten the text. The weekday is trimmed to six letters
for this reason.

**The smile looks like a frown.**
Check which way the curve bends: a mouth whose centre is higher than its
ends is a frown. The `happy` and `sad` formulas were swapped at first.

## Code structure slips

- **`SyntaxError` on an `if` line:** it needs a colon, not a semicolon.
- **`NameError` for a string:** text needs quotes, including URLs and
  WiFi credentials.
- **Mismatched names:** `request` and `requests`, `uct` and `utc`,
  `waln` and `wlan`, `API_key` and `api_key`. Python is case-sensitive
  and spelling-sensitive.
- **f-string placeholders** must be real variable names. Spaces aren't
  allowed.
- **Indentation:** everything inside an `if` or `def` must be indented by
  the same amount. An `elif` must line up with its `if`. Two `else:` in a
  row, or a stray `...` left from a snippet, are errors.
- **Variables created inside a function** aren't visible outside it.
- **Typing `...`** in place of code was a placeholder, not code.
- **Build in layers.** Print the raw response first, then extract fields,
  then format. It shows exactly which layer breaks.
