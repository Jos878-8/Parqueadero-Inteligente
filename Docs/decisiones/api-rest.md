# Decisiones de diseño de la API REST — Parqueadero Inteligente (Guía 4)

## Matriz de diseño (A1)

| Pregunta | Respuesta del equipo |
|---|---|
| ¿Qué recursos expondrá la API? | `devices` (dispositivos que han enviado telemetría, p. ej. PARK-001) y `measurements` (lecturas por espacio). Se conservan `parking`, `history` y `alerts` para el dashboard. |
| ¿Qué endpoint devuelve todos los dispositivos? | `GET /api/devices` |
| ¿Qué endpoint devuelve un dispositivo específico? | `GET /api/devices/{device_id}` |
| ¿Cómo se filtrarán mediciones por device_id? | Query parameter: `GET /api/measurements?device_id=PARK-001` (además `space_id`, `from`, `to`, `limit`, `offset`) |
| ¿Qué respuesta se espera si el dispositivo no existe? | `404 Not Found` con `{"detail": "Dispositivo no encontrado"}`. Una consulta de mediciones sin coincidencias NO es error: `200` y `[]`. |
| ¿Qué límite máximo de registros permitirá la API? | `limit` entre 1 y 100 (por defecto 20); `offset` ≥ 0. Fuera de rango responde `422`. |

## Justificación (≤150 palabras)

Usamos sustantivos en plural (`devices`, `measurements`) y el método GET, porque la acción ya está en el verbo HTTP. El dispositivo concreto va en la ruta (`/devices/{device_id}`) porque es un recurso con identidad propia; los filtros y la paginación van como query parameters porque modifican una colección sin crear endpoints nuevos. Limitamos `limit` a 100 para que ninguna solicitud devuelva toda la base: es una decisión académica, no una regla de REST. El dashboard y otros clientes consultan la API y no abren `parking.db`, de modo que podemos cambiar el almacenamiento sin reescribir los clientes. Los timestamps se manejan en UTC (ISO 8601), como el contrato de telemetría.

## Formato de respuesta de `GET /api/measurements`

```json
[
  {
    "id": 612,
    "message_id": "PARK-001-E06-000012",
    "device_id": "PARK-001",
    "timestamp": "2026-10-26T01:01:01.745263+00:00",
    "sequence": 12,
    "measurements": {"space_id": "E06", "occupied": true, "distance": 48.9, "parking_duration": 0.05},
    "received_at": "2026-10-26T01:01:01.746892+00:00"
  }
]
```

## Códigos HTTP

| Caso | Código |
|---|---|
| Consulta válida (con o sin resultados) | 200 |
| Telemetría válida recibida | 201 |
| `limit`/`offset`/fecha inválidos o body de POST inválido | 422 |
| `device_id` inexistente o ruta inexistente | 404 |
| Error inesperado | 500 |

## Compatibilidad

Las rutas oficiales son `/api/...`. Se mantiene el alias `/api/v1/...` (oculto en Swagger) para no romper el dashboard ni el simulador de entregas anteriores.
