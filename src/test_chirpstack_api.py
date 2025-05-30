import grpc
import chirpstack_api.api.device_pb2 as device_pb2
import chirpstack_api.api.device_pb2_grpc as device_pb2_grpc
from chirpstack_api import common

# API token
api_token = "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiJjaGlycHN0YWNrIiwiaXNzIjoiY2hpcnBzdGFjayIsInN1YiI6IjVlYmI5ZmMzLTViY2QtNGRkNC05ODIwLTdjY2RhZTM3MjIzMyIsInR5cCI6ImtleSJ9.h0gP7_8sLDIx6tdKIuhjUrl9eI61GwykrvryvAbSHu8"

# Metadata for authentication
auth_credentials = [('authorization', f'Bearer {api_token}')]

# Connect to the ChirpStack gRPC server
channel = grpc.insecure_channel("localhost:8080")
client = device_pb2_grpc.DeviceServiceStub(channel)

# Prepare and send the request
request = device_pb2.ListDevicesRequest(application_id="00feac3f-b311-457c-adbf-9b205304cd9b", limit=10)
response = client.List(request, metadata=auth_credentials)

# Print device DevEUIs
for device in response.result:
    print(f"Device: {device.name}, DevEUI: {device.dev_eui}")
