
import os
import paho.mqtt.client as mqtt
import json
import base64
import mysql.connector
import binascii
import threading
import sys
from datetime import datetime, timedelta

MYSQL_CONFIG = {
    'host': os.environ.get('DB_HOST'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('MYSQL_ROOT_PASSWORD'),
    'database': os.environ.get('DATABASE_NAME'),
    'port': 3306
}

def unpack_data(byteDataIn, port):
    dOut = {}
    if len(byteDataIn) == 13:
        port = 5
    match port:
        case 1:
            dOut.update({'soilTempCS': int.from_bytes(byteDataIn[0:2], 'big') / 10})
            dOut.update({'soilMoistS': int.from_bytes(byteDataIn[2:4], 'big') / 10})
            dOut.update({'soilTempCD': int.from_bytes(byteDataIn[4:6], 'big') / 10})
            dOut.update({'soilMoistD': int.from_bytes(byteDataIn[6:8], 'big') / 10})
        case 5:
            dOut.update({'soilTempCS': int.from_bytes(byteDataIn[0:2], 'big') / 10})
            dOut.update({'soilMoistS': int.from_bytes(byteDataIn[2:4], 'big') / 10})
            dOut.update({'soilTempCD': int.from_bytes(byteDataIn[4:6], 'big') / 10})
            dOut.update({'soilMoistD': int.from_bytes(byteDataIn[6:8], 'big') / 10})
            dOut.update({'airTempC': round(int.from_bytes(byteDataIn[8:10], 'big') / 1000, 2)})
            dOut.update({'airMoist': round(int.from_bytes(byteDataIn[10:12], 'big') / 1000, 2)})
            dOut.update({'batPct': round(int.from_bytes(byteDataIn[12:13], 'big') / 2.55, 2)})
        case 10:
            dOut.update({'airTemp': int.from_bytes(byteDataIn[0:2], 'big') / 100})
            dOut.update({'airHumid': int.from_bytes(byteDataIn[2:4], 'big') / 100})
            dOut.update({'airPresBar': int.from_bytes(byteDataIn[4:6], 'big') / 10000})
            dOut.update({'lightLux': int.from_bytes(byteDataIn[6:8], 'big') * 10})
            dOut.update({'minWindDir': int.from_bytes(byteDataIn[8:10], 'big')})
            dOut.update({'MaxWindDir': int.from_bytes(byteDataIn[10:12], 'big')})
            dOut.update({'avgWindDir': int.from_bytes(byteDataIn[12:14], 'big')})
            dOut.update({'minWindSp': int.from_bytes(byteDataIn[14:16], 'big') / 100})
            dOut.update({'maxWindSp': int.from_bytes(byteDataIn[16:18], 'big') / 100})
            dOut.update({'avgWindSp': int.from_bytes(byteDataIn[18:20], 'big') / 100})
            dOut.update({'accRain': int.from_bytes(byteDataIn[20:22], 'big') * 10})
            dOut.update({'accRainDur': int.from_bytes(byteDataIn[22:24], 'big') * 100})
            dOut.update({'rainInten': int.from_bytes(byteDataIn[24:26], 'big') / 10})
            dOut.update({'maxRain': int.from_bytes(byteDataIn[26:28], 'big') / 10})
            dOut.update({'pm_2_5': int.from_bytes(byteDataIn[28:30], 'big') / 10})
            dOut.update({'pm_10': int.from_bytes(byteDataIn[30:32], 'big') / 10})
            dOut.update({'c02': int.from_bytes(byteDataIn[32:34], 'big') / 10})
        case _:
            dOut.update({'rawData': binascii.hexlify(byteDataIn).decode('utf-8')})
    return dOut

def parse_gateway_phy_payload(phy_payload_bytes):
    total_len = len(phy_payload_bytes)
    if total_len < (1 + 7 + 1 + 4):
        return None
    mhdr = phy_payload_bytes[0:1]
    mac_payload = phy_payload_bytes[1:total_len - 4]
    mic = phy_payload_bytes[-4:]
    if len(mac_payload) < 8:
        return None
    fhdr = mac_payload[0:7]
    fport = mac_payload[7]
    frm_payload = mac_payload[8:]
    return {
        "mhdr": mhdr.hex(),
        "fhdr": fhdr.hex(),
        "fPort": fport,
        "frmPayload": frm_payload.hex(),
        "mic": mic.hex()
    }

def insert_data_into_mysql(dev_eui, timestamp, fport, sensor_values):
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        if fport == 10:
            sql = ('''
                INSERT INTO s1000_data (
                    devEui, timestamp, airTemp, airHumid, airPresBar, lightLux,
                    minWindDir, MaxWindDir, avgWindDir,
                    minWindSp, maxWindSp, avgWindSp,
                    accRain, accRainDur, rainInten, maxRain,
                    pm_2_5, pm_10, c02
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ''')
            values = [
                dev_eui, timestamp,
                sensor_values['airTemp'], sensor_values['airHumid'], sensor_values['airPresBar'], sensor_values['lightLux'],
                sensor_values['minWindDir'], sensor_values['MaxWindDir'], sensor_values['avgWindDir'],
                sensor_values['minWindSp'], sensor_values['maxWindSp'], sensor_values['avgWindSp'],
                sensor_values['accRain'], sensor_values['accRainDur'], sensor_values['rainInten'], sensor_values['maxRain'],
                sensor_values['pm_2_5'], sensor_values['pm_10'], sensor_values['c02']
            ]
        else:
            sql = "INSERT INTO sensor_data (devEui, timestamp, fPort, dataRaw) VALUES (%s, %s, %s, %s)"
            sensor_values_json = json.dumps(sensor_values)
            values = [dev_eui, timestamp, fport, sensor_values_json]

        cursor.execute(sql, values)
        conn.commit()
        conn.close()
    except mysql.connector.Error as e:
        print("Error inserting data into MySQL:", e)
        sys.stdout.flush()

def on_connect(client, userdata, flags, rc):
    print("✅ Connected to MQTT broker with result code", rc)
    result, mid = client.subscribe("#")
    print("📡 Subscribed to MQTT with result:", result)
    sys.stdout.flush()

def on_message(client, userdata, msg):
    # Split the topic and extract the devEui
    topic_parts = msg.topic.split('/')
    dev_eui = topic_parts[topic_parts.index("device") + 1] if "device" in topic_parts else None

    # Decode the payload to string if it's a bytes-like object
    try:
        payload_str = msg.payload.decode('utf-8')
        payload_data = json.loads(payload_str)  # Convert the string to a dictionary
    except UnicodeDecodeError as e:
        # print(f"Error decoding message payload: {e}")
        return
    except json.JSONDecodeError as e:
        # print(f"Error decoding JSON from payload: {e}")
        return

    # Now, you can check for "phyPayload" in the decoded dictionary
    if "phyPayload" in payload_data:
        try:
            # Extract phyPayload and decode it
            phy_payload_bytes = base64.b64decode(payload_data.get("phyPayload"))
        except Exception as e:
            print(f"Error decoding phyPayload: {e}")
            return
        parsed = parse_gateway_phy_payload(phy_payload_bytes)
        if not parsed:
            return
        fport = parsed.get("fPort")
        frm_payload_hex = parsed.get("frmPayload", "")
        try:
            sensor_bytes = bytes.fromhex(frm_payload_hex)
        except Exception as e:
            print(f"Error converting hex to bytes: {e}")
            return
        sensor_values = unpack_data(sensor_bytes, fport)
        timestamp = payload_data.get("time", None)
        insert_data_into_mysql(dev_eui, timestamp, fport, sensor_values)

    elif "data" in payload_data:
        # Handle raw data payload
        fport = payload_data.get("fPort")
        timestamp = payload_data.get("time")
        try:
            raw_bytes = base64.b64decode(payload_data.get("data"))
        except Exception as e:
            print(f"Error decoding data field: {e}")
            return
        sensor_values = unpack_data(raw_bytes, fport)
        insert_data_into_mysql(dev_eui, timestamp, fport, sensor_values)

def mqtt_thread():
    thread = threading.Thread(target=start_mqtt, daemon=True)
    thread.start()

def start_mqtt():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("mosquitto", 1883, 60)
    client.loop_start()

if __name__ == "__main__":
    mqtt_thread()
    while True:
        pass  # Keep main thread alive