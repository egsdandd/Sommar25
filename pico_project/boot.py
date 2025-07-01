# boot.py -- run on boot-up test1
from wifi import do_connect
from ntp_sync import sync_time
# This file is executed on every boot (including wake-boot from deepsleep)

print("Connecting to WiFi...")
do_connect()

sync_time()  # Synchronize time with NTP server
print("Time synchronized with NTP server!")