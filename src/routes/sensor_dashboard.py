from flask import Blueprint, render_template, request
import mysql.connector
import os

sensor_bp = Blueprint('sensor_bp', __name__)

MYSQL_CONFIG = {
    'host': os.environ.get('DB_HOST'),
    'user': os.environ.get('DB_USER'),
    'password': os.environ.get('MYSQL_ROOT_PASSWORD'),
    'database': os.environ.get('DATABASE_NAME'),
    'port': 3306
}

@sensor_bp.route("/sensor")
def sensor_dashboard():
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor(dictionary=True)

    sensors = []
    sensor_data = []
    upld_min = None
    lake_by_dev = {}
    valve_data = []
    current_valve = {}
    selected_dev = None
    graphs = []

    try:
        # Fetch available sensors
        cursor.execute("""
            SELECT DISTINCT devEui, devDescription
            FROM devices
            WHERE devEui IN (SELECT DISTINCT devEui FROM sensor_data)
            ORDER BY devDescription
        """)
        sensors = cursor.fetchall()

        selected_dev = request.args.get('devEui') or (sensors[0]['devEui'] if sensors else None)

        if selected_dev:
            cursor.execute("""
                SELECT timestamp, soilTempCS, soilTempCD, soilMoistS, soilMoistD, airTempC, airMoist, upldMin
                FROM sensor_data
                WHERE devEui = %s
                ORDER BY timestamp DESC LIMIT 240
            """, (selected_dev,))
            sensor_data = cursor.fetchall()[::-1]
            if sensor_data:
                upld_min = sensor_data[-1]['upldMin']

        # Lake-level data
        cursor.execute("""
            SELECT devEui, timestamp, lakeLevel, upldMin
            FROM sensor_data
            WHERE lakeLevel IS NOT NULL
            ORDER BY timestamp DESC
            LIMIT 300
        """)
        raw_lake = cursor.fetchall()
        for row in raw_lake:
            dev = row['devEui']
            lake_by_dev.setdefault(dev, []).append(row)

        for dev, rows in lake_by_dev.items():
            rows = rows[::-1][:240]
            label = f"Lake Level - {dev}"
            graphs.append({
                'label': label,
                'data': {
                    'labels': [r['timestamp'] for r in rows],
                    'values': [r['lakeLevel'] for r in rows]
                }
            })

        # Valve controller
        cursor.execute("""
            SELECT timestamp, vlvStatus, hPres, hFlow
            FROM sensor_data
            WHERE vlvStatus IS NOT NULL
            ORDER BY timestamp DESC LIMIT 240
        """)
        valve_data = cursor.fetchall()[::-1]
        if valve_data:
            current_valve = valve_data[-1]

    except Exception as e:
        print("Error loading sensor dashboard:", e)

    conn.close()

    return render_template("sensor_page.html",
        sensors=sensors,
        selected_dev=selected_dev,
        sensor_data=sensor_data,
        upld_min=upld_min,
        lake_data=lake_by_dev,
        valve_data=valve_data,
        current_valve=current_valve,
        graphs=graphs
    )
