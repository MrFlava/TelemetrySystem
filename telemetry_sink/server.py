import os
import json
import grpc
import asyncio
import signal
from cryptography.fernet import Fernet

from telemetry_sink.telemetry_pb2 import TelemetryResponse
import telemetry_sink.telemetry_pb2_grpc as telemetry_pb2_grpc
from telemetry_sink.utils import RateLimiter, flush_buffer_encrypted, periodic_flusher_encrypted

BUFFER_MAX_ITEMS = int(os.getenv("TELEMETRY_BUFFER_MAX_ITEMS", "100"))
FLUSH_INTERVAL_MS = int(os.getenv("TELEMETRY_FLUSH_INTERVAL_MS", "100"))
RATE_LIMIT_BPS = int(os.getenv("TELEMETRY_RATE_LIMIT_BPS", "10240"))
LOG_FILE = os.getenv("TELEMETRY_LOG_FILE", "telemetry_grpc.log")
ENCRYPTION_KEY = os.getenv("TELEMETRY_ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    raise RuntimeError("TELEMETRY_ENCRYPTION_KEY must be set")
fernet = Fernet(ENCRYPTION_KEY.encode())

_buffer = []
_buffer_lock = asyncio.Lock()
rate_limiter = RateLimiter(RATE_LIMIT_BPS)


class TelemetryService(telemetry_pb2_grpc.TelemetryServicer):
    async def SendTelemetry(self, request, context):
        item = {
            "sensor_name": request.sensor_name,
            "sensor_value": request.sensor_value,
            "timestamp": request.timestamp
        }
        raw = json.dumps(item, ensure_ascii=False)
        size = len(raw.encode("utf-8"))
        if not await rate_limiter.try_consume(size):
            context.set_code(grpc.StatusCode.RESOURCE_EXHAUSTED)
            context.set_details("Rate limit exceeded")
            return TelemetryResponse(status="rate_limited")
        async with _buffer_lock:
            _buffer.append(item)
            if len(_buffer) >= BUFFER_MAX_ITEMS:
                await flush_buffer_encrypted(_buffer, _buffer_lock, LOG_FILE)
        return TelemetryResponse(status="accepted")

async def serve():
    server = grpc.aio.server()
    telemetry_pb2_grpc.add_TelemetryServicer_to_server(TelemetryService(), server)
    server.add_insecure_port("[::]:50051")
    await server.start()
    flusher_task = asyncio.create_task(periodic_flusher_encrypted(_buffer, _buffer_lock, LOG_FILE, FLUSH_INTERVAL_MS, fernet))

    stop_event = asyncio.Event()

    def handle_signal():
        stop_event.set()

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, handle_signal)

    await stop_event.wait()
    await flush_buffer_encrypted(_buffer, _buffer_lock, LOG_FILE, fernet)
    await server.stop(5)
    flusher_task.cancel()

if __name__ == "__main__":
    asyncio.run(serve())
