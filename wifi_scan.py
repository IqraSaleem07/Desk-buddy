# Lists the WiFi networks the board can see.
# Your network must appear here, and it must be 2.4 GHz.
import network

wlan = network.WLAN(network.STA_IF)
wlan.active(True)

for ssid, bssid, channel, rssi, authmode, hidden in wlan.scan():
    print(ssid.decode(), "channel", channel, "signal", rssi)
