FROM python:3.10-slim

# Set the working directory
WORKDIR /src

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt  

# Copy the Flask app code into the container
COPY ./src /src

# Expose the Flask application port
EXPOSE 5000

# Start the Flask app using Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "web_server:app"]  
