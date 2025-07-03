# logging_helper.py
# Copyright (c) 2025, Dan-Håkan Davall
# Code free to use, modify, and distribute under the terms of the MIT License.

import utime, uos, gc

# Loggnivåer
logLevels = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
    "SCREEN": 60,
}

currentLogLevel = logLevels["INFO"]  # Change this to set the current log level
def set_log_level(level):
    global currentLogLevel
    if level in logLevels:
        currentLogLevel = logLevels[level]
    else:
        raise ValueError(f"Invalid log level: {level}")

# Controll if there is enough free space on the filesystem
# Returns True if there is enough free space, otherwise returns False
# This function checks if there is enough free space on the filesystem
# It uses the `uos.statvfs` function to get filesystem statistics
# It checks the free space in bytes and compares it to a minimum required space
# If the free space is greater than the minimum required space, it returns True
# Otherwise, it returns False
# The default minimum required space is set to 1024 bytes (1 KB)
# This function can be used to ensure that there is enough space for logging or other operations

def has_free_space(min_bytes=1024):
    stat = uos.statvfs('/')
    block_size = stat[0]
    free_blocks = stat[3]
    free_bytes = block_size * free_blocks
    return free_bytes > min_bytes  # min_bytes = minimum free space required

def Log(message, level="INFO"):
    if logLevels[level] >= currentLogLevel:
        timeStamp = utime.localtime()
        formattedTime = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
            timeStamp[0], timeStamp[1], timeStamp[2],
            timeStamp[3], timeStamp[4], timeStamp[5]
        )
        logMessage = f"[{formattedTime}] {level}: {message}"
        if currentLogLevel >= logLevels["SCREEN"]:
            print(logMessage)
        else:
            if has_free_space(1024):  # Kontrollera att minst 1 KB finns kvar
                with open("log.txt", "a") as logFile:
                    logFile.write(logMessage + "\n")
            else:
                print("Varning: Otillräckligt diskutrymme för loggning!")
