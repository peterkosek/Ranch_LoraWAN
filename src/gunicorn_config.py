def post_fork(server, worker):
    from data_handler import mqtt_thread
    print("🚀 Starting MQTT thread in Gunicorn worker")
    mqtt_thread()
