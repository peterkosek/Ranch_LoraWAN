from flask import Flask, render_template_string
import mysql.connector

app = Flask(__name__)

# Your existing config
MYSQL_CONFIG = {
    'host': 'localhost',
    'user': 'root',
    'password': 'ranch',
    'database': 'ranch_database'
}

@app.route('/')
def index():
    try:
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sensor_data ORDER BY timestamp DESC LIMIT 20")
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        conn.close()
    except Exception as e:
        return f"<h2>Error: {e}</h2>"

    # Simple HTML table render
    html = """
    <h2>Sensor Data</h2>
    <table border="1" cellpadding="5">
        <tr>{% for col in columns %}<th>{{ col }}</th>{% endfor %}</tr>
        {% for row in rows %}
        <tr>{% for cell in row %}<td>{{ cell }}</td>{% endfor %}</tr>
        {% endfor %}
    </table>
    """
    return render_template_string(html, columns=columns, rows=rows)

if __name__ == '__main__':
    app.run(debug=True)
