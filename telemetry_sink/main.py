import uvicorn
import argparse

from telemetry_sink.settings import APP_HOST, APP_PORT
from telemetry_sink.service import app

def run_server(host, port):
    uvicorn.run(app, host=host, port=port)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, default=APP_HOST)
    parser.add_argument("--port", type=int, default=APP_PORT)
    args = parser.parse_args()
    run_server(args.host, args.port)
