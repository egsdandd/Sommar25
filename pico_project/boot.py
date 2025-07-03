# boot.py -- run on boot-up test1
from wifi import connect_wifi
from ntp_sync import sync_time
# This file is executed on every boot (including wake-boot from deepsleep)

connect_wifi() # Connect to Wi-Fi to sync time

sync_time()  # Synchronize time with NTP server

# You can also use this file to run any initialization code.
# For example, you can import your main module here if you want it to run on boot
# try:
    # import main
# except ImportError:
#    print("main.py not found, skipping import.")
# If you have a main.py file, it will be executed automatically after this boot.py
# If you want to run a specific function from main.py, you can do it here:
