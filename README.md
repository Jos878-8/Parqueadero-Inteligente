# Parqueadero Inteligente — Proyecto Integrador IoT

Simulador de sensores de parqueadero → API REST (FastAPI) → SQLite → consulta por GET (Swagger / Dashboard).

## Arquitectura

```
simulator/generador.py  --POST /api/telemetry-->  backend (FastAPI)  --> parking.db (SQLite)
                                                       ^
                       Swagger (/docs) / dashboard --GET /api/devices | /api/measurements
```

## Instalación y ejecución

```bash
pip install -r requirements.txt

# 1. Backend (desde la raíz del proyecto)
uvicorn backend.main:app --reload --port 8000
#    Swagger: http://127.0.0.1:8000/docs

# 2. Simulador (otra terminal, desde la raíz)
python -m simulator.generador

# 3. Dashboard: abrir dashboard/index.html en el navegador
```

(El broker MQTT es opcional: si no está en `localhost:1883` el simulador solo envía por HTTP.)

## Endpoints

| Método | Ruta | Propósito |
|---|---|---|
| GET | `/health` | Estado del servicio |
| POST | `/api/telemetry` | Recibe y valida una lectura (201 / 422) |
| GET | `/api/devices` | Lista de dispositivos detectados |
| GET | `/api/devices/{device_id}` | Resumen de un dispositivo (404 si no existe) |
| GET | `/api/measurements` | Mediciones con filtros `device_id`, `space_id`, `from`, `to`, `limit` (1–100), `offset` |
| GET | `/api/parking` · `/api/history` · `/api/alerts` | Datos planos que usa el dashboard |

## Ejemplos

```bash
curl "http://127.0.0.1:8000/api/devices"
curl "http://127.0.0.1:8000/api/devices/PARK-001"
curl "http://127.0.0.1:8000/api/measurements?device_id=PARK-001&limit=10&offset=0"
curl "http://127.0.0.1:8000/api/measurements?device_id=PARK-001&from=2026-10-19T00:00:00Z&to=2026-10-19T23:59:59Z"
```

## Pruebas

```bash
python -m pytest -q
```

Las pruebas usan una base SQLite temporal; no dependen de `parking.db`.

## Estado y pendientes

- [x] Recepción, validación y persistencia (Guía 3)
- [x] Consulta de dispositivos y mediciones, filtros, paginación, histórico `from`/`to` (Guía 4)
- [ ] Dashboard consumiendo `/api/measurements` con filtros (siguiente etapa)

## Integrantes

- (completar nombres del equipo)
