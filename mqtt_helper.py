# mqtt_helper.py
# Copyright (c) 2025, Dan-Håkan Davall
# Code free to use, modify, and distribute under the terms of the MIT License.

from umqtt.simple import MQTTClient
import machine
import config

def connect_mqtt():
    try:
        client = MQTTClient(
            client_id="pico_w_client",
            server=config.mqtt_server,
            port=1883,
            user=config.mqtt_user,
            password=config.mqtt_password,
        )
        client.connect()
        print("Connected to MQTT")
        return client
    except Exception as e:
        print("MQTT connection failed:", e)
        machine.reset()  # Starta om om det inte funkar
