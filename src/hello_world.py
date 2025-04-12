import os
import paho.mqtt.client as mqtt
import json
import base64
import mysql.connector
import sys
import binascii
import threading
from flask import Flask, render_template_string, jsonify, redirect, url_for

app = Flask(__name__)

MYSQL_CONFIG = {
    'host': os.environ.get('DB_HOST'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('MYSQL_ROOT_PASSWORD'),
    'database': os.environ.get('DATABASE_NAME'),
    'port': 3306
}

@app.route('/')
def index():
    html = '''
    <!doctype html>
    <html lang="en">
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>Sensor Dashboard</title>
        <style>
            body { font-family: sans-serif; text-align: center; padding: 2em; }
            a { display: block; padding: 1em; margin: 1em 0; background: #00aaff; color: white; text-decoration: none; border-radius: 0.5em; }
        </style>
    </head>
    <body>
        <h2>Sensor Dashboard</h2>
        <a href="/temp-humid">Temperature, Humidity & Rain</a>
        <a href="/light-wind">Light & Wind</a>
        <a href="/air-quality">PM & CO₂</a>
        <a href="/wind-direction">Wind Direction</a>
    </body>
    </html>
    '''
    return html

@app.route('/wind-direction')
def wind_direction():
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, minWindDir, maxWindDir, avgWindDir FROM s1000_data ORDER BY timestamp DESC LIMIT 100")
        rows = cursor.fetchall()
        conn.close()

        timestamps = [r[0].strftime("%Y-%m-%d %H:%M:%S") for r in rows[::-1]]
        min_dir = [r[1] for r in rows[::-1]]
        max_dir = [r[2] for r in rows[::-1]]
        avg_dir = [r[3] for r in rows[::-1]]

        html = '''
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Wind Direction</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        </head>
        <body>
            <h2>Wind Direction (Latest 100)</h2>
            <label for="range">Zoom range (most recent N entries):</label>
            <input type="range" id="range" min="1" max="100" value="100" oninput="updateChart(this.value)">
            <canvas id="chart" width="360" height="250"></canvas>
            <script>
                const labelsFull = {{ labels | safe }};
                const minDirFull = {{ min | safe }};
                const maxDirFull = {{ max | safe }};
                const avgDirFull = {{ avg | safe }};

                const ctx = document.getElementById('chart').getContext('2d');
                const chart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: labelsFull,
                        datasets: [
                            { label: 'Min Wind Dir (\u00b0)', data: minDirFull, borderColor: 'gray', fill: false, tension: 0.1 },
                            { label: 'Max Wind Dir (\u00b0)', data: maxDirFull, borderColor: 'black', fill: false, tension: 0.1 },
                            { label: 'Avg Wind Dir (\u00b0)', data: avgDirFull, borderColor: 'blue', fill: false, tension: 0.1 }
                        ]
                    }
                });

                function updateChart(n) {
                    const count = parseInt(n);
                    chart.data.labels = labelsFull.slice(-count);
                    chart.data.datasets.forEach((ds, idx) => {
                        ds.data = [minDirFull, maxDirFull, avgDirFull][idx].slice(-count);
                    });
                    chart.update();
                }
            </script>
        </body>
        </html>
        '''

        return render_template_string(
            html,
            labels=json.dumps(timestamps),
            min=json.dumps(min_dir),
            max=json.dumps(max_dir),
            avg=json.dumps(avg_dir)
        )

    except Exception as e:
        return f"<h3>Error loading wind direction data: {e}</h3>"

# Original routes like /temp-humid, /light-wind, /air-quality need to be restored below.

@app.route('/data')
def raw_data():
    print("✅ /data route was called!", flush=True)
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 50")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return jsonify({"message": "No data in table yet."})

        return jsonify(rows)

    except Exception as e:
        return jsonify({"error": str(e)})

@app.route('/temp-humid')
def temp_humid():
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, airTemp, airHumid, accRain, rainInten, maxRain FROM s1000_data ORDER BY timestamp DESC LIMIT 50")
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return "<h3>No data available to plot yet.</h3>"

        timestamps = [r[0].strftime("%Y-%m-%d %H:%M:%S") for r in rows[::-1]]
        temps = [r[1] for r in rows[::-1]]
        humids = [r[2] for r in rows[::-1]]
        acc_rain = [r[3] for r in rows[::-1]]
        rain_inten = [r[4] for r in rows[::-1]]
        max_rain = [r[5] for r in rows[::-1]]

        latest_temp = temps[-1]
        latest_humid = humids[-1]

        html = '''
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Temperature, Humidity & Rain</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        </head>
        <body>
            <h2>Temperature, Humidity & Rain (Latest 50)</h2>
            <p>Current Temp: ''' + str(latest_temp) + ''' °F | Humidity: ''' + str(latest_humid) + '''%</p>
            <label for="range">Zoom range (most recent N entries):</label>
            <input type="range" id="range" min="1" max="50" value="50" oninput="updateChart(this.value)">
            <canvas id="chart" width="360" height="250"></canvas>
            <script>
                const labelsFull = {{ labels | safe }};
                const tempsFull = {{ temps | safe }};
                const humidsFull = {{ humids | safe }};
                const accRainFull = {{ acc_rain | safe }};
                const rainIntenFull = {{ rain_inten | safe }};
                const maxRainFull = {{ max_rain | safe }};

                const ctx = document.getElementById('chart').getContext('2d');
                const chart = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: labelsFull,
                        datasets: [
                            { label: 'Air Temp (°F)', data: tempsFull, borderColor: 'red', fill: false, tension: 0.1 },
                            { label: 'Humidity (%)', data: humidsFull, borderColor: 'blue', fill: false, tension: 0.1 },
                            { label: 'Accumulated Rain (in)', data: accRainFull, borderColor: 'green', fill: false, tension: 0.1 },
                            { label: 'Rain Intensity (in/hr)', data: rainIntenFull, borderColor: 'orange', fill: false, tension: 0.1 },
                            { label: 'Max Rain (in)', data: maxRainFull, borderColor: 'purple', fill: false, tension: 0.1 }
                        ]
                    }
                });

                function updateChart(n) {
                    const count = parseInt(n);
                    chart.data.labels = labelsFull.slice(-count);
                    chart.data.datasets.forEach((ds, idx) => {
                        ds.data = [tempsFull, humidsFull, accRainFull, rainIntenFull, maxRainFull][idx].slice(-count);
                    });
                    chart.update();
                }
            </script>
        </body>
        </html>
        '''

        return render_template_string(
            html,
            labels=json.dumps(timestamps),
            temps=json.dumps(temps),
            humids=json.dumps(humids),
            acc_rain=json.dumps(acc_rain),
            rain_inten=json.dumps(rain_inten),
            max_rain=json.dumps(max_rain)
        )

    except Exception as e:
        return f"<h3>Error loading data: {e}</h3>"

@app.route('/light-wind')
def light_wind():
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, lightLux, minWindSp, maxWindSp, avgWindSp, minWindDir, MaxWindDir, avgWindDir FROM s1000_data ORDER BY timestamp DESC LIMIT 50")
        rows = cursor.fetchall()
        conn.close()

        timestamps = [r[0].strftime("%Y-%m-%d %H:%M:%S") for r in rows[::-1]]
        light = [r[1] for r in rows[::-1]]
        min_sp = [r[2] for r in rows[::-1]]
        max_sp = [r[3] for r in rows[::-1]]
        avg_sp = [r[4] for r in rows[::-1]]
        min_dir = [r[5] for r in rows[::-1]]
        max_dir = [r[6] for r in rows[::-1]]
        avg_dir = [r[7] for r in rows[::-1]]

        html = '''
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Light & Wind</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        </head>
        <body>
            <h2>Light Intensity (lux)</h2>
            <canvas id="lightChart" width="360" height="250"></canvas>
            <h2>Wind Speed (MPH)</h2>
            <canvas id="windSpChart" width="360" height="250"></canvas>
            <h2>Wind Direction (°)</h2>
            <canvas id="windDirChart" width="360" height="250"></canvas>
            <script>
                const labels = {{ labels | safe }};
                new Chart(document.getElementById('lightChart'), {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [{ label: 'Light (lux)', data: {{ light | safe }}, borderColor: 'gold', fill: false }]
                    }
                });
                new Chart(document.getElementById('windSpChart'), {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [
                            { label: 'Min Speed', data: {{ min_sp | safe }}, borderColor: 'green', fill: false },
                            { label: 'Max Speed', data: {{ max_sp | safe }}, borderColor: 'red', fill: false },
                            { label: 'Avg Speed', data: {{ avg_sp | safe }}, borderColor: 'blue', fill: false }
                        ]
                    }
                });
                new Chart(document.getElementById('windDirChart'), {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [
                            { label: 'Min Dir', data: {{ min_dir | safe }}, borderColor: 'green', fill: false },
                            { label: 'Max Dir', data: {{ max_dir | safe }}, borderColor: 'red', fill: false },
                            { label: 'Avg Dir', data: {{ avg_dir | safe }}, borderColor: 'blue', fill: false }
                        ]
                    }
                });
            </script>
        </body>
        </html>
        '''
        return render_template_string(html, labels=json.dumps(timestamps), light=json.dumps(light), min_sp=json.dumps(min_sp), max_sp=json.dumps(max_sp), avg_sp=json.dumps(avg_sp), min_dir=json.dumps(min_dir), max_dir=json.dumps(max_dir), avg_dir=json.dumps(avg_dir))
    except Exception as e:
        return f"<h3>Error: {e}</h3>"
    
@app.route('/air-quality')
def air_quality():
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT timestamp, pm_2_5, pm_10, c02 FROM s1000_data ORDER BY timestamp DESC LIMIT 50")
        rows = cursor.fetchall()
        conn.close()

        timestamps = [r[0].strftime("%Y-%m-%d %H:%M:%S") for r in rows[::-1]]
        pm25 = [r[1] for r in rows[::-1]]
        pm10 = [r[2] for r in rows[::-1]]
        co2 = [r[3] for r in rows[::-1]]

        html = '''
        <!doctype html>
        <html lang="en">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
            <title>Air Quality</title>
            <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        </head>
        <body>
            <h2>Particulate Matter</h2>
            <canvas id="pmChart" width="360" height="250"></canvas>
            <h2>CO₂ (ppm)</h2>
            <canvas id="co2Chart" width="360" height="250"></canvas>
            <script>
                const labels = {{ labels | safe }};
                new Chart(document.getElementById('pmChart'), {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [
                            { label: 'PM2.5', data: {{ pm25 | safe }}, borderColor: 'orange', fill: false },
                            { label: 'PM10', data: {{ pm10 | safe }}, borderColor: 'brown', fill: false }
                        ]
                    }
                });
                new Chart(document.getElementById('co2Chart'), {
                    type: 'line',
                    data: {
                        labels: labels,
                        datasets: [
                            { label: 'CO₂ (ppm)', data: {{ co2 | safe }}, borderColor: 'black', fill: false }
                        ]
                    }
                });
            </script>
        </body>
        </html>
        '''
        return render_template_string(html, labels=json.dumps(timestamps), pm25=json.dumps(pm25), pm10=json.dumps(pm10), co2=json.dumps(co2))
    except Exception as e:
        return f"<h3>Error: {e}</h3>"


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
        print("DEBUG: fport =", fport)
        print("DEBUG: sensor_values =", sensor_values)
        sys.stdout.flush()

        if fport == 10:
            sql = ("""
                INSERT INTO s1000_data (
                    devEui, timestamp, airTemp, airHumid, airPresBar, lightLux,
                    minWindDir, MaxWindDir, avgWindDir,
                    minWindSp, maxWindSp, avgWindSp,
                    accRain, accRainDur, rainInten, maxRain,
                    pm_2_5, pm_10, c02
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """)
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
    topic_parts = msg.topic.split('/')
    dev_eui_topic = topic_parts[topic_parts.index("device") + 1] if "device" in topic_parts else None

    try:
        message = json.loads(msg.payload.decode("utf-8"))
    except Exception as e:
        print("Error decoding JSON:", e)
        return

    dev_eui = message.get("dev_eui") or message.get("DevEui") or dev_eui_topic or "unknown"

    if "phyPayload" in message:
        try:
            phy_payload_bytes = base64.b64decode(message.get("phyPayload"))
        except:
            try:
                phy_payload_bytes = bytes.fromhex(message.get("phyPayload"))
            except:
                return
        parsed = parse_gateway_phy_payload(phy_payload_bytes)
        if not parsed:
            return
        fport = parsed.get("fPort")
        frm_payload_hex = parsed.get("frmPayload", "")
        try:
            sensor_bytes = bytes.fromhex(frm_payload_hex)
        except:
            return
        sensor_values = unpack_data(sensor_bytes, fport)
        timestamp = message.get("time", None)
        insert_data_into_mysql(dev_eui, timestamp, fport, sensor_values)

    elif "data" in message:
        fport = message.get("fPort")
        timestamp = message.get("time")
        try:
            raw_bytes = base64.b64decode(message.get("data"))
        except:
            return
        sensor_values = unpack_data(raw_bytes, fport)
        print("💬 MQTT message received:")
        print("  ➤ dev_eui:", dev_eui)
        print("  ➤ fport:", fport)
        print("  ➤ timestamp:", timestamp)
        print("  ➤ sensor_values:", sensor_values)
        sys.stdout.flush()

        insert_data_into_mysql(dev_eui, timestamp, fport, sensor_values)

def start_flask():
    app.run(host='0.0.0.0', port=5000)

def start_mqtt():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.connect("mosquitto", 1883, 60)
    client.loop_start()
    
def mqtt_thread():
    thread = threading.Thread(target=start_mqtt, daemon=True)
    thread.start()

# mqtt_thread()


if __name__ == '__main__':
    mqtt_thread()
    start_flask()
