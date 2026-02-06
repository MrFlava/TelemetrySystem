# Telemetry System system and Sensors task

## TelemetrySystem setup Instructions

1. **Clone the repository**  
   `git clone <repo-url> && cd TelemetrySystem`

2. **Create venv and install requirements**  
   ```bash
    python -m venv <environment_name>
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    ```

3. If you want to use http service run commands 
   ```bash
   uvicorn telemetry_sink.main:app
   python sensor_node.py --sensor-name temp1 --rate 2 --sink-address http://localhost:8000/telemetry/

4. If you want to use grpc service run commands 
   ```bash
   python -m telemetry_sink.server
   python sensor_node_grpc.py --sensor-name SENSOR1 --sink-address localhost:50051 --rate 1

## Sensors task
* Start postgres with docker-compose:
   ```bash
   docker-compose up -d

* Connect to db and add tables with sql queries described in the sensors_task.db_tables.txt
* Run python script to fill sensors database
* ```bash
   cd sensors_task
   python data_insert.py