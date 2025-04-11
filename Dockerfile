FROM python:3.10

WORKDIR /src

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your updated Python code from ./src/ on host to /src in container
COPY . .

# CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--threads", "2", "hello-world:app"]
# CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--config", "gunicorn_config.py", "hello_world:app"]
# CMD ["gunicorn", "--bind", "0.0.0.0:5000", "hello_world:app", "-c", "gunicorn_config.py"]
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--config", "gunicorn_config.py", "web_server:app"]

# CMD ["python", "-u", "hello-world.py"]


