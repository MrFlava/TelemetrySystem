# telemetry_sink.py
import argparse
import asyncio
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, ValidationError
import uvicorn

class TelemetryData(BaseModel):
    sensor_name: str
    sensor_value: int
    timestamp: str

app = FastAPI()
received_data = []

@app.post("/telemetry")
async def receive_telemetry(data: TelemetryData):
    received_data.append(data)
    print(f"Received: {data}")
    return {"status": "ok"}

def run_server(host, port):
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default="0.0.0.0")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    run_server(args.host, args.port)
