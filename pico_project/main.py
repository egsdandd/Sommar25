# main.py
# Copyright (c) 2025, Dan-Håkan Davall
# Code free to use, modify, and distribute under the terms of the MIT License.

# Imports
from mqtt_helper import connect_mqtt
from logging_helper import Log, currentLogLevel, logLevels  # Importera loggningsfunktionen
import time
import dht
from machine import Pin, ADC
import gc

# Pin layout:
Log("Initializing onboard LED", "INFO")
led = Pin("LED", Pin.OUT)  # Alarm pin for external alarm - Inbyggd LED på Pico W

Log("Initializing DHT11 pin 11 for temp/hum", "INFO")
dht_sensor = dht.DHT11(Pin(11))  # DHT11 sensor on GPIO 15

Log("Initializing VCC buzzer pin 5", "INFO")
buzzerVCC = Pin(5, Pin.OUT)  # VCC for buzzer

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
    Log(f"Raw ADC value: {adc_value}, Voltage: {volt:.2f}V, Raw Temperature: {raw_temperature:.2f}°C, Calibrated Temperature: {calibrated_temperature:.2f}°C", "DEBUG")
    return raw_temperature, calibrated_temperature, volt

# Flash led        
def FlashLed(noOfTimes):
    print("Flashing LED", noOfTimes, "times")
    led.off() # Make sure led is off
    for i in range(noOfTimes,0,-1): 
        led.on()
        time.sleep(1)
        led.off()
        time.sleep(1)
    time.sleep(1)

# Flash led to indicate startup
Log("Starting up...", "INFO")
# Flash LED to indicate startup
FlashLed(1)

# Huvudfunktion för att läsa sensordata och skicka till MQTT

# DHT22-sensor
def read_DHT22():
    dht_sensor.measure()
    temperature = dht_sensor.temperature()
    humidity = dht_sensor.humidity()
    print("Temperature:", temperature, "°C, Humidity:", humidity, "%")
    return temperature, humidity

def outlier_Deleter(value_Array):
    value_Array = sorted(value_Array)
    n = len(value_Array)
    q1_Pos = (n + 1) / 4
    q3_Pos = 3 * (n + 1) / 4
    # This function is used to calculate the quartile values
    def qurtile_calc(pos):
        lower = value_Array[int(pos)-1]
        upper = value_Array[int(pos)]
        return lower + (pos%1)*(upper - lower)
    q1 = qurtile_calc(q1_Pos) # quartile 1
    q3 = qurtile_calc(q3_Pos)# quartile 1
    iqr = q3-q1# inter quartile range
    lower_Bound = q1 - (1.5*iqr)
    upper_Bound = q3 + (1.5*iqr)
    filtered_array = list(filter(lambda x:lower_Bound<=x<=upper_Bound,value_Array))
    return filtered_array

def moisture_Precent(curr_Val):  
    dry_Soil_Value = 65535 # Max value, Wet soil
    wet_Soil_Value = 0 # Min value, Desert 
    percent = (curr_Val - dry_Soil_Value) * (100) / (wet_Soil_Value - dry_Soil_Value)
    return round(percent, 2)

def read_Sensor_Average(samples, plant_Reader, plantVCC):
    total = []
    return_Array = []

    for _ in range(samples): # Run samples time
        plantVCC.value(1)  
        time.sleep(0.005)
        single_Mesure_Array = []
        for sensor in plant_Reader: # Loop over all plants
            single_Mesure_Array.append(sensor.read_u16()) # Create array [Value plant1, Value plant2,...]
        total.append(single_Mesure_Array) # Create array [[Value plant1, Value plant2,...],[Value plant1, Value plant2,...]]
        plantVCC.value(0)  
        time.sleep(0.005)
    for i in range(len(plant_Reader)):# Loop over the number of plants 
        clean_Value_array = outlier_Deleter([row[i] for row in total]) # Take out the values associate with the plant and clean the array from outliers
        moisture = moisture_Precent(sum(clean_Value_array) / len(clean_Value_array)) # Send the average value of the raw values to calculate the precentage between 0-100
        return_Array.append(moisture) # Append mosture level to retrun array [Moist_Level_Plant_1, Moist_Level_Plant_2,...]
    gc.collect()  # Delete nonsense data, Keep memory free!
    return return_Array

def plant_Monitor (plantVCC,sensorArray):
    sampleSize = 5
    moistureData = []
    return_Array = []
    for _ in range (sampleSize): #As the mesurmement of soil is noizy I collect 5 moisture value per plant
        plant_moist_Value = read_Sensor_Average(sampleSize,sensorArray, plantVCC) # Collect moisture value
        moistureData.append(plant_moist_Value)
    
    for i in range(len(sensorArray)):
        moisture_Plant = outlier_Deleter([row[i] for row in moistureData]) # Take out the values associate with the plant and clean the array from outliers
        moisture = sum(moisture_Plant) / len(moisture_Plant) # Calculate the mean value of the clean array
        return_Array.append(moisture) # Append mosture level to retrun array [Mean_Moist_Level_Plant_1, Mean_Moist_Level_Plant_2,...]
    gc.collect()  # Delete nonsense data, Keep memory free!
    return return_Array

def main():
     # Sätt loggnivå (kan ändras här)
    currentLogLevel = logLevels["INFO"]
    
    Log("Starting up...", "INFO")
    client = connect_mqtt()
    
    while True:
        try:
            ADC_temperature, ADC_calibrated_temperature, ADC_voltage = read_calibrated_temperature()
            print("ADC Temperature:", ADC_temperature, "°C")

            temperature, humidity = read_DHT22()

            print("SensorVCC state:", sensorVCC.value() )
            moist = plant_Monitor(sensorVCC,[soil_Sensor1,soil_Sensor2]) 
            plant_Left_Moist_Level = moist[0]
            plant_Right_Moist_Level = moist[1]

            print("Plant Left Moisture Level:", plant_Left_Moist_Level, "%")
            print("Plant Right Moisture Level:", plant_Right_Moist_Level, "%")
            plants =[
                ["left",plant_Right_Moist_Level,50],
                ["right",plant_Left_Moist_Level,50]
            ]
            print("Plants:", plants)
            #Log(f"Temperature: {temperature}°C, Humidity: {humidity}%, ADC Temperature: {ADC_temperature}°C, Moisture Left: {plant_Left_Moist_Level}%, Moisture Right: {plant_Right_Moist_Level}%", "DEBUG")    
        except Exception as e:
            print("Sensor read failed:", e)
            time.sleep(300)
            continue
        try:
            FlashLed(1)  # Flash LED to indicate data read
            # Publish data to MQTT broker
            client.publish("egsdand/feeds/picow_temp", str(temperature))
            client.publish("egsdand/feeds/picow_hum", str(humidity))
            # client.publish("egsdand/feeds/adc_temp", str(ADC_temperature))
            client.publish("egsdand/feeds/moisture1", str(plant_Left_Moist_Level))
            client.publish("egsdand/feeds/moisture2", str(plant_Right_Moist_Level))
            # client.publish("egsdand/feeds/plants", str(plants))
            client.publish("egsdand/feeds/adc_calibrated_temp", str(ADC_calibrated_temperature))
            # client.publish("egsdand/feeds/adc_voltage", str(ADC_voltage))
            print("Data published successfully")
        except Exception as e:
            print("Publish failed:", e)
        time.sleep(10)

main()
