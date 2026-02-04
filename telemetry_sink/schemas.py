from pydantic import BaseModel

class TelemetryData(BaseModel):
    sensor_name: str
    sensor_value: int
    timestamp: str
