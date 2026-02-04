import asyncio
from datetime import datetime
import random

import httpx
import argparse

async def send_telemetry(client, url, sensor_name):
    value = random.randint(0, 100)
    payload = {
        "sensor_name": sensor_name,
        "sensor_value": value,
        "timestamp": datetime.utcnow().isoformat()
    }
    try:
        resp = await client.post(url, json=payload, timeout=5)
        resp.raise_for_status()
    except Exception as e:
        print(f"Failed to send data: {e}")

async def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--rate", type=float, default=1.0)
    parser.add_argument("--sensor-name", type=str, required=True)
    parser.add_argument("--sink-address", type=str, required=True)
    args = parser.parse_args()

    interval = 1.0 / args.rate
    async with httpx.AsyncClient() as client:
        while True:
            await send_telemetry(client, args.sink_address, args.sensor_name)
            await asyncio.sleep(interval)


if __name__ == "__main__":
    asyncio.run(main())