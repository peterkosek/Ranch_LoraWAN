import os
from flask import Flask, request, jsonify, render_template_string, render_template
import mysql.connector
from datetime import timedelta
from routes.temp_humid import bp as temp_humid_bp

app = Flask(__name__)
app.register_blueprint(temp_humid_bp)

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

@app.route('/temp-humid-rain-page')
def temp_humid_rain_page():
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
  <title>Charts Debug</title>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <style>
    canvas { margin-bottom: 40px; border: 1px solid #ccc; }
    .chart-container { max-width: 900px; margin: auto; }
  </style>
</head>
<body>
  <div class="chart-container">
    <h1>JS Debug Test</h1>
    <canvas id="temperatureChart" height="150"></canvas>
  </div>

  <!-- Move JS here, at the bottom -->
  <script>
    console.log("🌟 JS is running at the bottom");

    fetch('/api/temp-humid-rain')
      .then(res => res.json())
      .then(data => {
        console.log("🎯 Got data:", data);
        const canvas = document.getElementById("temperatureChart");
        const ctx = canvas.getContext("2d");

        new Chart(ctx, {
          type: 'line',
          data: {
            labels: data[0].data.labels,
            datasets: [{
              label: data[0].label,
              data: data[0].data.values,
              borderColor: 'blue',
              borderWidth: 2,
              fill: false,
              tension: 0.1
            }]
          }
        });
      })
      .catch(err => {
        console.error("❌ Fetch failed:", err);
      });
  </script>
</body>
</html>
""")

@app.route('/environmental-page')
def environmental_page():
    return render_template('environmental_page.html')

@app.route('/template-test')
def template_test():
    from os import listdir
    return str(listdir("templates"))

@app.route('/air-quality-page')
def air_quality_page():
    return render_template('air_quality_page.html')

@app.route('/wind-page')
def wind_light_page():
    return render_template('wind_page.html')
    

@app.route('/rain-page')
def rain_page():
    return render_template('rain_page.html')

@app.route('/')
def index():
    return "Hello, world!"

def fetch_graph_data(columns, range=1, limit=100):
    conn = mysql.connector.connect(**MYSQL_CONFIG)
    cursor = conn.cursor()

    graph_data = []
    for column, label in columns:
        records_to_fetch = range * 240

        query = f"""
            SELECT timestamp, {column}
            FROM s1000_data
            WHERE timestamp >= NOW() - INTERVAL {records_to_fetch} HOUR
            ORDER BY timestamp DESC
            LIMIT {limit}
        """

        cursor.execute(query)
        rows = cursor.fetchall()

        if rows:
            labels = [r[0] for r in rows]
            values = [r[1] for r in rows]
            graph_data.append({
                'label': label,
                'data': {'labels': labels, 'values': values}
            })

    cursor.close()
    conn.close()
    return graph_data


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
