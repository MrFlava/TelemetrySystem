import json
import asyncio
from time import monotonic
from typing import List

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

async def write_to_file(lines: List[str], log_file: str) -> None:
    def _sync_write():
        with open(log_file, "a", encoding="utf-8") as f:
            f.writelines(lines)
    await asyncio.to_thread(_sync_write)

async def flush_buffer(buffer, buffer_lock, log_file):
    async with buffer_lock:
        if not buffer:
            return
        to_flush = buffer.copy()
        buffer.clear()
    lines = [json.dumps(item, ensure_ascii=False) + "\n" for item in to_flush]
    await write_to_file(lines, log_file)

async def periodic_flusher(buffer, buffer_lock, log_file, flush_interval_ms):
    interval = max(0.001, flush_interval_ms / 1000.0)
    while True:
        await asyncio.sleep(interval)
        await flush_buffer(buffer, buffer_lock, log_file)


async def flush_buffer_encrypted(buffer, buffer_lock, log_file, fernet):
    async with buffer_lock:
        if not buffer:
            return
        to_flush = buffer.copy()
        buffer.clear()
    lines = []
    for item in to_flush:
        raw = json.dumps(item, ensure_ascii=False)
        encrypted = fernet.encrypt(raw.encode("utf-8"))
        lines.append(encrypted.decode("utf-8") + "\n")
    def _sync_write():
        with open(log_file, "a", encoding="utf-8") as f:
            f.writelines(lines)
    await asyncio.to_thread(_sync_write)

async def periodic_flusher_encrypted(buffer, buffer_lock, log_file, interval_ms, encryptor):
    interval = max(0.001, interval_ms / 1000.0)
    while True:
        await asyncio.sleep(interval)
        await flush_buffer_encrypted(buffer, buffer_lock, log_file, encryptor)