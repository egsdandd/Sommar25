# ntp_sync.py
import ntptime
import machine

def sync_time(timezone_offset=0):
    """
    Synkroniserar tiden med NTP-servern och justerar för tidszon.
    timezone_offset: antal timmar att lägga till UTC (t.ex. 2 för svensk sommartid)
    """
    try:
        print("Synchronizing time with NTP server...")
        ntptime.settime()
        rtc = machine.RTC()
        print("Current time UTC:", rtc.datetime())
        year, month, day, weekday, hour, minute, second, subsec = rtc.datetime()
        hour += timezone_offset
        rtc.datetime((year, month, day, weekday, hour, minute, second, subsec))
        print("Current time LocalTime:", rtc.datetime())
        return True
    except Exception as e:
        print("Failed to synchronize time:", e)
        return False
    print("Time synchronized with NTP server!")
    