import os
import json
import asyncio
from typing import List

from fastapi import FastAPI, HTTPException

from telemetry_sink.schemas import TelemetryData
from telemetry_sink.utils import RateLimiter, flush_buffer, periodic_flusher

# Configuration
BUFFER_MAX_ITEMS = int(os.getenv("TELEMETRY_BUFFER_MAX_ITEMS", "100"))
FLUSH_INTERVAL_MS = int(os.getenv("TELEMETRY_FLUSH_INTERVAL_MS", "100"))
RATE_LIMIT_BPS = int(os.getenv("TELEMETRY_RATE_LIMIT_BPS", "10240"))
LOG_FILE = os.getenv("TELEMETRY_LOG_FILE", "telemetry.log")

app = FastAPI()

_buffer: List[dict] = []
_buffer_lock = asyncio.Lock()
rate_limiter = RateLimiter(RATE_LIMIT_BPS)

@app.post("/telemetry/")
async def receive_telemetry(data: TelemetryData):
    item = data.dict()
    raw = json.dumps(item, ensure_ascii=False)
    size = len(raw.encode("utf-8"))

    if not await rate_limiter.try_consume(size):
        raise HTTPException(status_code=429, detail="Rate limit exceeded")

    async with _buffer_lock:
        _buffer.append(item)
        if len(_buffer) >= BUFFER_MAX_ITEMS:
            await flush_buffer(_buffer, _buffer_lock, LOG_FILE)

    return {"status": "accepted"}

@app.on_event("startup")
async def startup():
    asyncio.create_task(periodic_flusher(_buffer, _buffer_lock, LOG_FILE, FLUSH_INTERVAL_MS))
