import asyncio
import random
from datetime import datetime

import grpc
import argparse

from telemetry_sink import telemetry_pb2
from telemetry_sink import telemetry_pb2_grpc

async def send_telemetry(stub, sensor_name):
    value = random.randint(0, 100)
    request = telemetry_pb2.TelemetryRequest(
        sensor_name=sensor_name,
        sensor_value=value,
        timestamp=datetime.utcnow().isoformat()
    )
    try:
        response = await stub.SendTelemetry(request)
        print(f"Status: {response.status}")
    except Exception as e:
        print(f"Failed to send data: {e}")

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rate", type=float, default=1.0)
    parser.add_argument("--sensor-name", type=str, required=True)
    parser.add_argument("--sink-address", type=str, required=True)
    args = parser.parse_args()

    interval = 1.0 / args.rate
    async with grpc.aio.insecure_channel(args.sink_address) as channel:
        stub = telemetry_pb2_grpc.TelemetryStub(channel)
        while True:
            await send_telemetry(stub, args.sensor_name)
            await asyncio.sleep(interval)

if __name__ == "__main__":
    asyncio.run(main())
