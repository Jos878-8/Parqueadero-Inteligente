from datetime import datetime

from pydantic import BaseModel, Field, field_validator


def parse_iso8601(value: str) -> datetime:
    """Interpreta ISO 8601 aceptando 'Z' al final (UTC)."""
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


# ---------- Entrada (POST /api/telemetry) ----------

class MeasurementsIn(BaseModel):
    space_id: str = Field(min_length=1)
    occupied: bool
    distance: float = Field(ge=0, le=400)           # cm (valid_min / valid_max del config)
    parking_duration: float = Field(ge=0, le=1440)  # minutos


class TelemetryIn(BaseModel):
    message_id: str = Field(min_length=1)
    device_id: str = Field(min_length=1)
    timestamp: str
    sequence: int = Field(ge=0)
    measurements: MeasurementsIn

    @field_validator("timestamp")
    @classmethod
    def timestamp_must_be_iso8601(cls, value: str) -> str:
        try:
            parse_iso8601(value)
        except ValueError:
            raise ValueError("timestamp debe estar en formato ISO 8601")
        return value


# ---------- Salida (GET) ----------

class MeasurementsOut(BaseModel):
    space_id: str
    occupied: bool
    distance: float
    parking_duration: float


class MeasurementOut(BaseModel):
    id: int
    message_id: str | None
    device_id: str
    timestamp: str
    sequence: int | None
    measurements: MeasurementsOut
    received_at: str | None


class DeviceOut(BaseModel):
    device_id: str
    measurement_count: int
    space_count: int
    last_timestamp: str | None
    last_received_at: str | None


class DeviceDetailOut(DeviceOut):
    spaces: list[str]
