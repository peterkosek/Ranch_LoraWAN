import os
from flask import Flask, request, jsonify
import mysql.connector
from datetime import timedelta

app = Flask(__name__)

# Fetching environment variables from Docker container
MYSQL_HOST = os.getenv('DB_HOST', 'mysql')  # Defaults to 'mysql' if not set
MYSQL_USER = os.getenv('DB_USER', 'root')  # Defaults to 'root'
MYSQL_PASSWORD = os.getenv('MYSQL_ROOT_PASSWORD', 'ranch')  # Defaults to 'ranch'
MYSQL_DATABASE = os.getenv('DATABASE_NAME', 'ranch_database')  # Defaults to 'ranch_database'

# MySQL connection configuration
MYSQL_CONFIG = {
    'host': MYSQL_HOST,
    'user': MYSQL_USER,
    'password': MYSQL_PASSWORD,
    'database': MYSQL_DATABASE
}

def fetch_graph_data(time_range):
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()

        graph_data = []

        columns = [("temp", "Temperature"), ("humidity", "Humidity"), ("rain", "Rainfall")]
        for column, label in columns:
            records_to_fetch = time_range * 24  # Fetch data for the specified number of hours (24 per day)

            query = f"""
                SELECT timestamp, {column} 
                FROM s1000_data 
                WHERE timestamp >= NOW() - INTERVAL {records_to_fetch} HOUR
                ORDER BY timestamp DESC
                LIMIT %s
            """
            cursor.execute(query, (records_to_fetch,))
            rows = cursor.fetchall()

            if not rows:
                continue

            rows = rows[::-1]  # Reverse the rows to ensure chronological order

            labels = [r[0] + timedelta(hours=8) for r in rows]  # Adjust for timezone if needed
            values = [r[1] for r in rows]

            filtered_values = [v if v != 0 else None for v in values]  # Handle zero values

            graph_data.append({
                "label": label,
                "labels": [str(l) for l in labels],
                "values": filtered_values
            })

        return graph_data
    except Exception as e:
        print(f"Error fetching data: {e}")
        return []
    finally:
        cursor.close()
        conn.close()

@app.route('/temp-humid-rain', methods=['GET'])
def temp_humid_rain():
    time_range = request.args.get('range', default=1, type=int)  # Get the range from the request
    graphs = fetch_graph_data(time_range)
    return jsonify(graphs)

@app.route('/')
def index():
    return "Hello, world!"


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
