"""API REST del Parqueadero Inteligente (FastAPI).

Ejecutar desde la raíz del proyecto:
    uvicorn backend.main:app --reload --port 8000
Swagger:  http://127.0.0.1:8000/docs
"""
from contextlib import asynccontextmanager

from fastapi import APIRouter, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from backend.alerts import check_occupancy_alert
from backend.database import (
    get_alerts,
    get_device_summary,
    get_history,
    get_latest_telemetry,
    init_database,
    list_devices,
    list_measurements,
    save_telemetry,
)
from backend.schemas import (
    DeviceDetailOut,
    DeviceOut,
    MeasurementOut,
    TelemetryIn,
    parse_iso8601,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_database()  # crea tablas aunque no se ejecute como script
    yield


app = FastAPI(
    title="API Parqueadero Inteligente IoT",
    description="Recibe telemetría del simulador, la persiste en SQLite y la expone por consulta.",
    version="1.1.0",
    lifespan=lifespan,
)

# El dashboard (HTML/JS) se abre desde otro origen, igual que con el Flask anterior.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)

router = APIRouter()


def _validate_date(value: str | None, name: str) -> str | None:
    if value is None:
        return None
    try:
        parse_iso8601(value)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail=f"El parámetro '{name}' debe estar en formato ISO 8601 (UTC), "
                   f"por ejemplo 2026-10-19T00:00:00Z",
        )
    return value


# ---------------------------- Guía 3: recepción ----------------------------

@router.post("/telemetry", status_code=201, tags=["Telemetría"])
def receive_telemetry(payload: TelemetryIn):
    data = payload.model_dump()
    save_telemetry(data)
    alert = check_occupancy_alert(data)

    response = {"message": "Telemetría recibida correctamente"}
    if alert:
        response["alert"] = alert
    return response


# ---------------------------- Guía 4: consulta -----------------------------

@router.get("/measurements", response_model=list[MeasurementOut], tags=["Mediciones"])
def get_measurements(
    device_id: str | None = None,
    space_id: str | None = None,
    date_from: str | None = Query(default=None, alias="from",
                                  description="Inicio del rango (ISO 8601, UTC)"),
    date_to: str | None = Query(default=None, alias="to",
                                description="Fin del rango (ISO 8601, UTC)"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
):
    date_from = _validate_date(date_from, "from")
    date_to = _validate_date(date_to, "to")
    if date_from and date_to and parse_iso8601(date_from) > parse_iso8601(date_to):
        raise HTTPException(status_code=422, detail="'from' no puede ser posterior a 'to'")

    return list_measurements(
        device_id=device_id,
        space_id=space_id,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )


@router.get("/devices", response_model=list[DeviceOut], tags=["Dispositivos"])
def get_devices():
    return list_devices()


@router.get("/devices/{device_id}", response_model=DeviceDetailOut, tags=["Dispositivos"])
def get_device(device_id: str):
    device = get_device_summary(device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Dispositivo no encontrado")
    return device


# ------------- Endpoints que ya consume el dashboard (formato plano) --------

@router.get("/parking", tags=["Dashboard"])
def get_parking():
    return get_latest_telemetry()


@router.get("/history", tags=["Dashboard"])
def get_history_data():
    return get_history()


@router.get("/alerts", tags=["Dashboard"])
def get_alerts_data():
    return get_alerts()


@app.get("/health", tags=["Estado"])
def health():
    return {"status": "ok"}


@app.get("/", tags=["Estado"])
def home():
    return {"message": "API Parqueadero IoT funcionando"}


# Ruta oficial de la guía (/api/...) y alias /api/v1/... para no romper
# el simulador ni el dashboard de las entregas anteriores.
app.include_router(router, prefix="/api")
app.include_router(router, prefix="/api/v1", include_in_schema=False)
