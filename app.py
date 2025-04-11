from flask import Flask
import mysql.connector

app = Flask(__name__)

@app.route('/')
def index():
    try:
        conn = mysql.connector.connect(
            host="mysql",  # service name in docker-compose
            user="root",
            password="ranch",
            database="ranch_database"
        )
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM sensor_data")
        row_count = cursor.fetchone()[0]
        conn.close()
        return f"<h2>Sensor data count: {row_count}</h2>"
    except Exception as e:
        return f"<h2>Error: {e}</h2>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

