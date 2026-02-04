import os
import json
import asyncio
from time import monotonic
from typing import List

from fastapi import FastAPI, HTTPException

from telemetry_sink.schemas import TelemetryData

# Configuration
BUFFER_MAX_ITEMS = int(os.getenv("TELEMETRY_BUFFER_MAX_ITEMS", "100"))
FLUSH_INTERVAL_MS = int(os.getenv("TELEMETRY_FLUSH_INTERVAL_MS", "100"))  # milliseconds
RATE_LIMIT_BPS = int(os.getenv("TELEMETRY_RATE_LIMIT_BPS", "10240"))  # bytes per second
LOG_FILE = os.getenv("TELEMETRY_LOG_FILE", "telemetry.log")

app = FastAPI()

# In-memory buffer and lock
_buffer: List[dict] = []
_buffer_lock = asyncio.Lock()

# Rate limiter
class RateLimiter:
    def __init__(self, rate_bytes_per_sec: int):
        self.rate = float(rate_bytes_per_sec)
        self.capacity = float(rate_bytes_per_sec)
        self.tokens = self.capacity
        self.last = monotonic()
        self._lock = asyncio.Lock()

    async def try_consume(self, n_bytes: int) -> bool:
        async with self._lock:
            now = monotonic()
            elapsed = now - self.last
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last = now
            if self.tokens >= n_bytes:
                self.tokens -= n_bytes
                return True
            return False

rate_limiter = RateLimiter(RATE_LIMIT_BPS)

async def _write_to_file(lines: List[str]) -> None:
    def _sync_write():
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.writelines(lines)
    await asyncio.to_thread(_sync_write)

async def _flush_buffer() -> None:
    async with _buffer_lock:
        if not _buffer:
            return
        to_flush = _buffer.copy()
        _buffer.clear()
    lines = [json.dumps(item, ensure_ascii=False) + "\n" for item in to_flush]
    await _write_to_file(lines)

async def _periodic_flusher() -> None:
    interval = max(0.001, FLUSH_INTERVAL_MS / 1000.0)
    while True:
        await asyncio.sleep(interval)
        await _flush_buffer()


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
            await _flush_buffer()

    return {"status": "accepted"}

# @app.on_event("startup")
# async def startup():
#     asyncio.create_task(_periodic_flusher())
