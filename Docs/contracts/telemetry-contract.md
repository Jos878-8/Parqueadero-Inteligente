# Contrato de Telemetría — Parqueadero Inteligente

## 1. Descripción

El contrato de telemetría define el formato de los mensajes generados por el simulador del parqueadero inteligente.

Cada mensaje representa una lectura realizada por el dispositivo y contiene información de identificación, tiempo, secuencia y las mediciones del espacio de parqueadero.

## 2. Estructura del mensaje

Cada mensaje debe contener obligatoriamente los siguientes campos:

| Campo | Tipo | Obligatorio | Descripción |
|---|---|---|---|
| `message_id` | string | Sí | Identificador único de la lectura |
| `device_id` | string | Sí | Identificador del dispositivo |
| `timestamp` | string | Sí | Fecha y hora de generación de la lectura |
| `sequence` | integer | Sí | Número consecutivo de la lectura |
| `measurements` | object | Sí | Contiene las variables medidas |

## 3. Mediciones

El objeto `measurements` contiene las variables del parqueadero:

| Variable | Tipo | Unidad | Descripción |
|---|---|---|---|
| `occupied` | boolean | No aplica | Indica si el espacio está ocupado |
| `distance` | number | cm | Distancia detectada por el sensor |
| `parking_duration` | number | segundos | Tiempo que el vehículo lleva ocupando el espacio |

## 4. Identificación

`message_id` debe identificar de manera única cada mensaje.

`device_id` identifica el dispositivo que genera las lecturas.

El campo `sequence` debe ser un número entero consecutivo para facilitar la identificación del orden de los mensajes.

## 5. Timestamp

El campo `timestamp` debe utilizar el formato ISO 8601.

Ejemplo:

`2026-09-06T21:00:00Z`

La zona horaria utilizada en el ejemplo es UTC.

## 6. Reglas de validación

Un mensaje válido debe cumplir las siguientes reglas:

- Todos los campos obligatorios deben estar presentes.
- `message_id` debe ser de tipo string.
- `device_id` debe ser de tipo string.
- `timestamp` debe utilizar formato ISO 8601.
- `sequence` debe ser un número entero.
- `measurements` debe ser un objeto.
- `occupied` debe ser booleano.
- `distance` debe ser numérico.
- `parking_duration` debe ser numérico.
- Las mediciones deben mantenerse dentro de los rangos definidos por el equipo.

## 7. Ejemplo de mensaje válido

```json
{
  "message_id": "PARK-001-000001",
  "device_id": "PARK-001",
  "timestamp": "2026-09-06T21:00:00Z",
  "sequence": 1,
  "measurements": {
    "occupied": true,
    "distance": 15.5,
    "parking_duration": 60
  }
}
