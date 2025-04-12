from flask import Blueprint, jsonify, request
import mysql.connector
import os

bp = Blueprint('temp_humid', __name__)

MYSQL_CONFIG = {
    'host': os.getenv('DB_HOST', 'mysql'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('MYSQL_ROOT_PASSWORD', 'ranch'),
    'database': os.getenv('DATABASE_NAME', 'ranch_database'),
}

@bp.route('/api/temp-humid-rain')
def temp_humid_rain():
    try:
        range_param = request.args.get('range', default=1, type=int)
        columns = [
            ('airTemp', 'Temperature'),
            ('airHumid', 'Humidity'),
            ('accRain', 'Rain')
        ]
        graphs = fetch_graph_data(columns, range=range_param, limit=10)
        return jsonify(graphs)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route('/api/environmental')
def api_environmental():
    columns = [
        ('airTemp', 'Temperature'),
        ('airHumid', 'Humidity'),
        ('airPresBar', 'Pressure'),
        ('lightLux', 'LightLux')
    ]
    return jsonify(fetch_graph_data(columns, limit=240))

@bp.route('/api/air-quality')
def api_air_quality():
    columns = [
        ('pm_2_5', 'PM 2.5'),
        ('pm_10', 'PM 10'),
        ('c02', 'CO2')
    ]
    return jsonify(fetch_graph_data(columns, limit=240))


@bp.route('/api/wind')
def api_wind():
    columns = [
        ('minWindSp', 'MinWindSp'),
        ('avgWindSp', 'AvgWindSp'),
        ('maxWindSp', 'MaxWindSp'),
        ('minWindDir', 'MinWindDir'),
        ('avgWindDir', 'AvgWindDir'),
        ('maxWindDir', 'MaxWindDir')
    ]
    return jsonify(fetch_graph_data(columns, limit=240))


@bp.route('/api/rain')
def api_rain():
    columns = [
        ('accRain', 'AccRain'),
        ('accRainDur', 'AccRainDur'),
        ('rainInten', 'RainInten'),
        ('maxRain', 'MaxRain')
    ]
    return jsonify(fetch_graph_data(columns, limit=240))


def fetch_graph_data(columns, range=1, limit=10):
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()

    graph_data = []
    for column, label in columns:
        query = f"""
            SELECT timestamp, {column}
            FROM s1000_data
            ORDER BY timestamp DESC
            LIMIT {limit}
        """
        cursor.execute(query)
        rows = cursor.fetchall()

        if rows:
            labels = [r[0].strftime('%Y-%m-%d %H:%M:%S') for r in rows]
            values = [r[1] for r in rows]
            graph_data.append({
                'label': label,
                'data': {'labels': labels, 'values': values}
            })

    cursor.close()
    conn.close()
    return graph_data
