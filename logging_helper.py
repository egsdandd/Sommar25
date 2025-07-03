# logging_helper.py
# Copyright (c) 2025, Dan-Håkan Davall
# Code free to use, modify, and distribute under the terms of the MIT License.

import utime

# Loggnivåer
logLevels = {
    "DEBUG": 10,
    "INFO": 20,
    "WARNING": 30,
    "ERROR": 40,
    "CRITICAL": 50,
    "SCREEN": 60,
}

currentLogLevel = logLevels["INFO"]  # Byt till "SCREEN" för att skriva till skärm

def Log(message, level="INFO"):
    if logLevels[level] >= currentLogLevel:
        timeStamp = utime.localtime()
        formattedTime = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
            timeStamp[0], timeStamp[1], timeStamp[2],
            timeStamp[3], timeStamp[4], timeStamp[5]
        )
        logMessage = f"[{formattedTime}] {level}: {message}"
        if currentLogLevel >= logLevels["SCREEN"]:
            print(logMessage)  # Skriv till skärm om loggnivån är "SCREEN" eller högre
        else:
            with open("log.txt", "a") as logFile:
                logFile.write(logMessage + "\n")
