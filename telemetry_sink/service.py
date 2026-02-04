import uvicorn
from fastapi import FastAPI

from telemetry_sink.schemas import TelemetryData

app = FastAPI()
received_data = []

@app.post("/telemetry")
async def receive_telemetry(data: TelemetryData):
    received_data.append(data)
    print(f"Received: {data}")
    return {"status": "ok"}

