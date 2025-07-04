# main.py
# Copyright (c) 2025, Dan-Håkan Davall
# Code free to use, modify, and distribute under the terms of the MIT License.

# Imports
from mqtt_helper import connect_mqtt
from logging_helper import Log, currentLogLevel, logLevels  # Importera loggningsfunktionen
import time
import dht
import machine
from machine import Pin, ADC, PWM
import gc
from wifi import connect_wifi, disconnect_wifi, is_connected, get_ip_address, get_network_info, get_signal_strength, get_mac_address

# Pin layout:
Log("Initializing onboard LED", "INFO")
led = Pin("LED", Pin.OUT)  # Alarm pin for external alarm - Inbyggd LED på Pico W

Log("Initializing DHT11 pin 11 for temp/hum", "INFO")
dht_sensor = dht.DHT11(Pin(11))  # DHT11 sensor on GPIO 15

Log("Initializing VCC buzzer pin 5", "INFO")
buzzerVCC = PWM(Pin(5))  # VCC for buzzer
buzzerVCC.freq(440)  # Set frequency to 1kHz
Log("Initializing VCC soil pin 15", "INFO")
sensorVCC = Pin(15, Pin.OUT)  # VCC for soilsensor

Log("Initializing soil sensor1 pin 27", "INFO")
soil_Sensor1 = ADC(Pin(27))  # Soil moisture sensor on GPIO 27

Log("Initializing soil sensor2 pin 28", "INFO")
soil_Sensor2 = ADC(Pin(28))  # Soil moisture sensor on GPIO 28

Log("Initializing ADC(4) for temperature measurement", "INFO")
adc = machine.ADC(4) # ADC for temperature measurement on core

# 
VREF_ACTUAL = 3.3  # Mät denna med multimeter
TEMP_OFFSET = 0.0  # Justera baserat på känd referenstemperatur
TEMP_SLOPE_CORRECTION = 1.0  # Finjustera om nödvändigt
            
# Funktion för att läsa och kalibrera temperatur från ADC
# Använder en 16-bitars ADC och konverterar till grader Celsius
def read_calibrated_temperature():
    adc_value = adc.read_u16()
    volt = (VREF_ACTUAL / 65535) * adc_value
    raw_temperature = 27 - (volt - 0.706) / 0.001721
    calibrated_temperature = (raw_temperature * TEMP_SLOPE_CORRECTION) + TEMP_OFFSET
    # Log(f"Raw ADC value: {adc_value}, Voltage: {volt:.2f}V, Raw Temperature: {raw_temperature:.2f}°C, Calibrated Temperature: {calibrated_temperature:.2f}°C", "DEBUG")
    return raw_temperature, calibrated_temperature, volt

# Flash led        
def FlashLed(noOfTimes):
    # print("Flashing LED", noOfTimes, "times")
    led.off() # Make sure led is off
    for i in range(noOfTimes,0,-1): 
        led.on()
        time.sleep(1)
        led.off()
        time.sleep(1)
    time.sleep(1)

# Buzzer function to beep a specified number of times
# This function will turn on the buzzer for 1 second, then off for 1 second, repeating for the specified number of times.
# It is used to indicate startup or other events.        
def Buzzer(noOfTimes):
    print("Beeping", noOfTimes, "times")
    buzzerVCC.duty_u16(0) # Make sure buzzer is off
    for i in range(noOfTimes,0,-1): 
        buzzerVCC.duty_u16(32768)  # Set duty cycle to 50% (32768 out of 65535)
        time.sleep(1)
        buzzerVCC.duty_u16(0) # Set duty cycle to 0% (off)
        time.sleep(1)
    time.sleep(1)

# Flash led to indicate startup
Log("Starting up...", "INFO")
Buzzer(1) # Beep once to indicate startup

# DHT22-sensor

def read_DHT22():
    try:
        dht_sensor.measure()  # Measure temperature and humidity
        time.sleep(2)         # DHT22 requires a 2-second delay to stabilize after power-up
        temperature = dht_sensor.temperature()  # Gets temperature in Celsius
        if temperature is None: 
            Log("Failed to read temperature from DHT22", "ERROR") # If temperature reading fails, log an error
            return None, None
        humidity = dht_sensor.humidity()        # Gets humidity in percentage
        if humidity < 0 or humidity > 100:  # Check if humidity is within valid range
            Log("Humidity reading out of range (0-100%)", "ERROR") # If humidity is out of range, log an error
            return None, None
        if humidity is None: # If humidity reading fails, log an error
            Log("Failed to read humidity from DHT22", "ERROR") # If humidity reading fails, log an error
            return None, None
        return temperature, humidity
    except Exception as e:
        Log(f"Exception occurred while reading DHT22: {e}", "ERROR")
        return None, None


def outlier_Deleter(value_Array):
    value_Array = sorted(value_Array) # Sort the array to calculate quartiles
    n = len(value_Array) # Number of values in the array
    q1_Pos = (n + 1) / 4 # Quartile 1 position
    q3_Pos = 3 * (n + 1) / 4 # Quartile 3 position
    # This function is used to calculate the quartile values
    def qurtile_calc(pos):
        lower = value_Array[int(pos)-1] # Lower value of the quartile
        upper = value_Array[int(pos)] # Upper value of the quartile
        return lower + (pos%1)*(upper - lower) # Interpolate between lower and upper value
    q1 = qurtile_calc(q1_Pos) # quartile 1
    q3 = qurtile_calc(q3_Pos)# quartile 3
    iqr = q3-q1# inter quartile range
    lower_Bound = q1 - (1.5*iqr) # Lower bound for outliers
    upper_Bound = q3 + (1.5*iqr) # Upper bound for outliers
    filtered_array = list(filter(lambda x:lower_Bound<=x<=upper_Bound,value_Array)) # Filter the array to remove outliers
    return filtered_array

def moisture_Precent(curr_Val):  
    dry_Soil_Value = 65535 # Max value, Wet soil
    wet_Soil_Value = 0 # Min value, Desert 
    percent = (curr_Val - dry_Soil_Value) * (100) / (wet_Soil_Value - dry_Soil_Value) # Calculate the percentage of moisture
    if percent < 0: # If the percentage is less than 0, set it to 0
        percent = 0
    return round(percent, 2)

def read_Sensor_Average(samples, plant_Reader, plantVCC): # Read soil sensors and return average moisture levels
    total = [] # Array to hold all measurements
    return_Array = [] # Array to hold the final moisture levels for each plant
    for _ in range(samples): # Run samples time
        plantVCC.value(1)  # Turn on VCC for soil sensors
        time.sleep(0.005) # Wait for sensors to stabilize
        single_Mesure_Array = [] # Array to hold single measurements for each plant
        for sensor in plant_Reader: # Loop over all plants
            single_Mesure_Array.append(sensor.read_u16()) # Create array [Value plant1, Value plant2,...]
        # print("Single measurement array:", single_Mesure_Array) # Print the single measurement array
        total.append(single_Mesure_Array) # Create array [[Value plant1, Value plant2,...],[Value plant1, Value plant2,...]]
        plantVCC.value(0)  # Turn off VCC for soil sensors
        time.sleep(0.005)
    for i in range(len(plant_Reader)):# Loop over the number of plants 
        clean_Value_array = outlier_Deleter([row[i] for row in total]) # Take out the values associate with the plant and clean the array from outliers
        moisture = moisture_Precent(sum(clean_Value_array) / len(clean_Value_array)) # Send the average value of the raw values to calculate the precentage between 0-100
        return_Array.append(moisture) # Append mosture level to retrun array [Moist_Level_Plant_1, Moist_Level_Plant_2,...]
    gc.collect()  # Delete nonsense data, Keep memory free!
    return return_Array

def plant_Monitor (plantVCC,sensorArray):
    sampleSize = 5 # Number of samples to take for each plant
    moistureData = [] # Array to hold moisture values for each plant
    return_Array = [] # Array to hold the final moisture levels for each plant
    for _ in range (sampleSize): #As the mesurmement of soil is noizy I collect 5 moisture value per plant
        plant_moist_Value = read_Sensor_Average(sampleSize,sensorArray, plantVCC) # Collect moisture value
        moistureData.append(plant_moist_Value) # Append the moisture value to the moistureData array
    
    for i in range(len(sensorArray)): # Loop over the number of plants
        moisture_Plant = outlier_Deleter([row[i] for row in moistureData]) # Take out the values associate with the plant and clean the array from outliers
        moisture = sum(moisture_Plant) / len(moisture_Plant) # Calculate the mean value of the clean array
        return_Array.append(moisture) # Append mosture level to retrun array [Mean_Moist_Level_Plant_1, Mean_Moist_Level_Plant_2,...]
    gc.collect()  # Delete nonsense data, Keep memory free!
    return return_Array

def is_mqtt_connected(client):
    try:
        # Försök att pinga brokern (om stöds)
        client.ping()
        return True
    except Exception as e:
        Log(f"MQTT connection lost: {e}", "ERROR")
        return False


def main():
     # Define log level
    currentLogLevel = logLevels["INFO"]
    
    Log("Starting up...", "INFO")
    Log("Starting up...", "DEBUG")
    Log("Starting up...", "ERROR")
    if not is_connected():
        Log("Not connected to Wi-Fi...connecting", "INFO")
        connect_wifi()

    client = connect_mqtt()

    if not is_mqtt_connected(client):
        Log("Not connected to MQTT...reconnecting", "INFO")
        client = connect_mqtt()

    while True:
        try:
            ADC_temperature, ADC_calibrated_temperature, ADC_voltage = read_calibrated_temperature() # Read and calibrate temperature from ADC
            if ADC_temperature is None or ADC_calibrated_temperature is None:
                Log("Failed to read temperature from ADC", "ERROR")
                continue  # Skip to the next iteration if reading fails

            print("ADC calibrated Temperature:", ADC_calibrated_temperature, "°C") 

            temperature, humidity = read_DHT22() # Read temperature and humidity from DHT22 sensor

            moist = plant_Monitor(sensorVCC,[soil_Sensor1,soil_Sensor2]) # Read soil moisture levels for both plants
            if moist is None or len(moist) < 2:
                Log("Failed to read moisture levels from sensors", "ERROR")
                continue
            plant_Left_Moist_Level = moist[0] # Get moisture level for left plant
            plant_Right_Moist_Level = moist[1] # Get moisture level for right plant
            print("Plant Left Moisture Level:", plant_Left_Moist_Level, "%")
            print("Plant Right Moisture Level:", plant_Right_Moist_Level, "%")

        except Exception as e: # Handle any exceptions that occur during sensor reading
            print("Sensor read failed:", e)
            
            time.sleep(300) # Wait for 5 minutes before retrying
            continue
        try:
            connect_wifi()  # Connect to Wi-Fi
            time.sleep(1)  # Wait for Wi-Fi to stabilize
            if not is_connected():  # Check if Wi-Fi is connected
                Log("Not connected to Wi-Fi...connecting", "INFO")
                print("Connecting to Wi-Fi...")
                connect_wifi()  # Connect to Wi-Fi
            #client = connect_mqtt() # Connect to MQTT broker
    
            FlashLed(2)  # Flash LED to indicate data read
            #Buzzer(1)
            # Publish data to MQTT broker
            client.publish("egsdand/feeds/picow_temp", str(temperature))
            client.publish("egsdand/feeds/picow_hum", str(humidity))

            client.publish("egsdand/feeds/moisture1", str(plant_Left_Moist_Level))
            client.publish("egsdand/feeds/moisture2", str(plant_Right_Moist_Level))

            client.publish("egsdand/feeds/adc_calibrated_temp", str(ADC_calibrated_temperature))

            # client.publish("egsdand/feeds/adc_voltage", str(ADC_voltage))
            # client.publish("egsdand/feeds/adc_temp", str(ADC_temperature))
            # client.publish("egsdand/feeds/plants", str(plants))
            
            print("Data published successfully")
            # Buzzer(2)
            disconnect_wifi() # Disconnect from WIFI

        except Exception as e: # Handle any exceptions that occur during MQTT publishing
            print("MQTT publish failed:", e)
            Log(f"MQTT publish failed: {e}", "ERROR")

        time.sleep(120) # Wait for 2 minutes before the next iteration
        # Free up memory
        gc.collect()  # Collect garbage to free up memory


main()
