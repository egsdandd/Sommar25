# wifi.py
import network
import time
import config
import machine
from machine import Pin

led = Pin("LED", Pin.OUT)  # Alarm pin for external alarm - Inbyggd LED på Pico W
led.off()  # Turn off the LED as a starting point

def do_connect():
    led.on()  # Turn on the LED to indicate connection attempt
    wlan = network.WLAN(network.STA_IF) # Station mode
    wlan.active(True) # Activate the WLAN interface
    if not wlan.isconnected(): # Check if already connected
        print('Connecting to WiFi...')
        wlan.connect(config.ssid, config.password) # Connect to the Wi-Fi network using SSID and password from config
        print('Waiting for connection...ssid:', config.ssid) # Print the SSID being connected to
        while not wlan.isconnected(): # Wait until connected
            time.sleep(0.5)
    print('Connected to Wi-Fi:', wlan.ifconfig())
    led.off()  # Turn off the LED to indicate successful connection

def disconnect_wifi(): # Disconnect from Wi-Fi
    wlan = network.WLAN(network.STA_IF) # Station mode
    if wlan.isconnected(): # Check if connected
        print('Disconnecting from Wi-Fi...') 
        wlan.disconnect() # Disconnect from the Wi-Fi network
        time.sleep(1) # Wait for a second to ensure disconnection
        if wlan.isconnected(): # Check if still connected after attempting to disconnect
            # If still connected, reset the machine to ensure no Wi-Fi remains active
            print("Disconnect has failed :(, It left me no choice")
            machine.reset()  # Hard reset, im not allowing the pico to keep wifi on under any circumstance
        else:
            print("Great success, we have disconnected!")
    else:
        print("Not connected to Wi-Fi.")

def is_connected():
    wlan = network.WLAN(network.STA_IF) # Station mode
    return wlan.isconnected() # Check if the WLAN interface is connected to a network

def get_ip_address():
    wlan = network.WLAN(network.STA_IF)
    if wlan.isconnected():
        return wlan.ifconfig()[0]  # Return the IP address
    else:
        return None

def get_network_info():
    wlan = network.WLAN(network.STA_IF)
    if wlan.isconnected(): # Check if connected
        # Return a dictionary with network information
        return { 
            'ssid': wlan.config('essid'),
            'ip': wlan.ifconfig()[0],
            'subnet': wlan.ifconfig()[1],
            'gateway': wlan.ifconfig()[2],
            'dns': wlan.ifconfig()[3]
        }
    else:
        return None

def get_signal_strength(): # Get the signal strength of the connected Wi-Fi network
    wlan = network.WLAN(network.STA_IF)
    if wlan.isconnected():
        return wlan.status('rssi')  # Return the signal strength in dBm
    else:
        return None

def get_mac_address(): # Get the MAC address of the connected Wi-Fi interface
    wlan = network.WLAN(network.STA_IF)
    if wlan.isconnected():
        return wlan.config('mac')  # Return the MAC address
    else:
        return None

def get_network_status():
    wlan = network.WLAN(network.STA_IF)
    if wlan.isconnected():
        return {
            'status': 'connected',
            'ip': wlan.ifconfig()[0],
            'signal_strength': wlan.status('rssi')
        }
    else:
        return {
            'status': 'disconnected'
        }

def scan_networks():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    networks = wlan.scan()
    return [{'ssid': net[0].decode('utf-8'), 'rssi': net[3]} for net in networks]  # Return SSID and signal strength

def connect_to_network(ssid, password):
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print(f'Connecting to network {ssid}...')
        wlan.connect(ssid, password)
        while not wlan.isconnected():
            time.sleep(0.5)
    print('Connected to Wi-Fi:', wlan.ifconfig())   

def disconnect_from_network():
    wlan = network.WLAN(network.STA_IF)
    if wlan.isconnected():
        print('Disconnecting from network...')
        wlan.disconnect()
        time.sleep(1)
        if wlan.isconnected():
            print("Disconnect has failed :(, It left me no choice")
            machine.reset()  # Hard reset, im not allowing the pico to keep wifi on under any circumstance
        else:
            print("Great success, we have disconnected!")
    else:
        print("Not connected to any network.")

def reconnect():
    wlan = network.WLAN(network.STA_IF)
    if wlan.isconnected():
        print('Reconnecting to network...')
        wlan.disconnect()
        time.sleep(1)
        wlan.connect(config.ssid, config.password)
        while not wlan.isconnected():
            time.sleep(0.5)
        print('Reconnected to Wi-Fi:', wlan.ifconfig())
    else:
        print("Not connected to any network, connecting now...")
        connect_to_network(config.ssid, config.password)

def get_wifi_status(): # Get the current Wi-Fi connection status
    wlan = network.WLAN(network.STA_IF)
    if wlan.isconnected():
        return {
            'status': 'connected',
            'ip': wlan.ifconfig()[0],
            'signal_strength': wlan.status('rssi')
        }
    else:
        return {
            'status': 'disconnected'
        }

def get_wifi_info(): # Get detailed information about the current Wi-Fi connection
    wlan = network.WLAN(network.STA_IF)
    if wlan.isconnected():
        return {
            'ssid': wlan.config('essid'),
            'ip': wlan.ifconfig()[0],
            'subnet': wlan.ifconfig()[1],
            'gateway': wlan.ifconfig()[2],
            'dns': wlan.ifconfig()[3],
            'mac': wlan.config('mac'),
            'signal_strength': wlan.status('rssi')
        }
    else:
        return None
    