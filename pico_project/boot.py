import network
import time
import ntptime
import machine
import config
# boot.py -- run on boot-up test1

def do_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect(config.ssid, config.password)
        print('Waiting for connection...ssid:', config.ssid)
        while not wlan.isconnected():
            time.sleep(0.5)
    print('Connected to Wi-Fi:', wlan.ifconfig())

print("Connecting to WiFi...")
do_connect()
print("WiFi connected successfully!")

try:
    print("Synchronizing time with NTP server...")
    ntptime.settime()
    rtc = machine.RTC()
    print("Current time UTC:", rtc.datetime())
    year, month, day, weekday, hour, minute, second, subsec = rtc.datetime()

    # Justera för tidszon: här lägger vi till 2 timmar för svensk sommertid (UTC+2)
    hour += 2

    rtc.datetime((year, month, day, weekday, hour, minute, second, subsec))   
    print("Current time LocalTime:", rtc.datetime())

except Exception as e:
    print("Failed to synchronize time:", e)