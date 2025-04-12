import paho.mqtt.client as mqtt
import json
import base64
import os

MQTT_BROKER = os.getenv("MQTT_BROKER", "mosquitto")
MQTT_PORT = int(os.getenv("MQTT_PORT", "1883"))
APP_ID = os.getenv("APP_ID", "1")  # set this to match your application

def send_downlink(dev_eui, fport, data, confirmed=True):
    """
    Send a LoRaWAN downlink to a device via ChirpStack MQTT.

    Args:
    - dev_eui (str): The target device's DevEUI
    - fport (int): FPort to send the message on
    - data (bytes | str | list[int]): Raw bytes, base64 string, or list of uint8_t
    - confirmed (bool): Whether this should be a confirmed downlink
    """
    # Handle input types
    if isinstance(data, bytes):
        b64_data = base64.b64encode(data).decode('utf-8')
    elif isinstance(data, str):
        b64_data = data  # assume already base64
    elif isinstance(data, list):
        try:
            b64_data = base64.b64encode(bytes(data)).decode('utf-8')
        except Exception as e:
            raise TypeError("Failed to convert list to base64:", e)
    else:
        raise TypeError("data must be bytes, base64 str, or list of integers")

    # Construct topic and payload
    topic = f"application/{APP_ID}/device/{dev_eui.lower()}/command/down"
    payload = {
        "confirmed": confirmed,
        "fPort": fport,
        "data": b64_data
    }

    # Publish
    client = mqtt.Client()
    client.connect(MQTT_BROKER, MQTT_PORT, 60)
    client.publish(topic, json.dumps(payload))
    client.disconnect()
    print(f"📡 Confirmed downlink sent to {dev_eui} on fPort {fport}")
