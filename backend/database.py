"""Acceso a SQLite del Parqueadero Inteligente.

La ruta de la base se calcula respecto a la raíz del proyecto (no respecto al
directorio desde el que se ejecuta), así el backend siempre abre el mismo
parking.db. Para pruebas se puede cambiar con la variable PARKING_DB.
"""
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

DB_PATH = os.getenv(
    "PARKING_DB",
    str(Path(__file__).resolve().parent.parent / "parking.db"),
)


def get_connection():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def init_database():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS telemetry (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_id TEXT,
            device_id TEXT NOT NULL,
            space_id TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            sequence INTEGER,
            occupied INTEGER NOT NULL,
            distance REAL NOT NULL,
            parking_duration REAL NOT NULL,
            received_at TEXT
        )
    """)

    # Migración: la base de la guía anterior no tenía received_at.
    columns = [row["name"] for row in cursor.execute("PRAGMA table_info(telemetry)")]
    if "received_at" not in columns:
        cursor.execute("ALTER TABLE telemetry ADD COLUMN received_at TEXT")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            space_id TEXT NOT NULL,
            message TEXT NOT NULL,
            parking_duration REAL NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    cursor.execute(
        "CREATE INDEX IF NOT EXISTS idx_telemetry_device ON telemetry(device_id)"
    )

    connection.commit()
    connection.close()


# ---------------------------------------------------------------------------
# ESCRITURA (Guía 3)
# ---------------------------------------------------------------------------

def save_telemetry(data):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO telemetry (
            message_id, device_id, space_id, timestamp, sequence,
            occupied, distance, parking_duration, received_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("message_id"),
        data["device_id"],
        data["measurements"]["space_id"],
        data["timestamp"],
        data.get("sequence"),
        int(data["measurements"]["occupied"]),
        data["measurements"]["distance"],
        data["measurements"]["parking_duration"],
        datetime.now(timezone.utc).isoformat(),
    ))

    connection.commit()
    connection.close()


def save_alert(space_id, message, parking_duration, timestamp):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO alerts (space_id, message, parking_duration, timestamp)
        VALUES (?, ?, ?, ?)
    """, (space_id, message, parking_duration, timestamp))

    connection.commit()
    connection.close()


# ---------------------------------------------------------------------------
# CONSULTAS PARA EL DASHBOARD ACTUAL (se mantienen planas para no romperlo)
# ---------------------------------------------------------------------------

def get_latest_telemetry():
    connection = get_connection()
    rows = connection.execute("""
        SELECT t.*
        FROM telemetry t
        INNER JOIN (
            SELECT space_id, MAX(id) AS max_id
            FROM telemetry
            GROUP BY space_id
        ) latest ON t.id = latest.max_id
        ORDER BY t.space_id
    """).fetchall()
    connection.close()
    return [dict(row) for row in rows]


def get_history():
    connection = get_connection()
    rows = connection.execute(
        "SELECT * FROM telemetry ORDER BY id DESC LIMIT 100"
    ).fetchall()
    connection.close()
    return [dict(row) for row in rows]


def get_alerts():
    connection = get_connection()
    rows = connection.execute(
        "SELECT * FROM alerts ORDER BY id DESC LIMIT 100"
    ).fetchall()
    connection.close()
    return [dict(row) for row in rows]


# ---------------------------------------------------------------------------
# CONSULTAS DE LA GUÍA 4
# ---------------------------------------------------------------------------

def _row_to_measurement(row) -> dict:
    """Convierte una fila plana de SQLite al formato del contrato JSON:
    las variables medidas vuelven agrupadas en el objeto `measurements`."""
    return {
        "id": row["id"],
        "message_id": row["message_id"],
        "device_id": row["device_id"],
        "timestamp": row["timestamp"],
        "sequence": row["sequence"],
        "measurements": {
            "space_id": row["space_id"],
            "occupied": bool(row["occupied"]),
            "distance": row["distance"],
            "parking_duration": row["parking_duration"],
        },
        "received_at": row["received_at"],
    }


def list_measurements(
    device_id: str | None = None,
    space_id: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> list[dict]:
    sql = """
        SELECT id, message_id, device_id, space_id, timestamp, sequence,
               occupied, distance, parking_duration, received_at
        FROM telemetry
    """
    conditions = []
    params: list = []

    if device_id:
        conditions.append("device_id = ?")
        params.append(device_id)
    if space_id:
        conditions.append("space_id = ?")
        params.append(space_id)
    # datetime() de SQLite normaliza a UTC textos ISO con "Z" o "+00:00".
    if date_from:
        conditions.append("datetime(timestamp) >= datetime(?)")
        params.append(date_from)
    if date_to:
        conditions.append("datetime(timestamp) <= datetime(?)")
        params.append(date_to)

    if conditions:
        sql += " WHERE " + " AND ".join(conditions)

    sql += " ORDER BY id DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    connection = get_connection()
    rows = connection.execute(sql, params).fetchall()
    connection.close()
    return [_row_to_measurement(row) for row in rows]


_DEVICE_SELECT = """
    SELECT device_id,
           COUNT(*) AS measurement_count,
           COUNT(DISTINCT space_id) AS space_count,
           MAX(timestamp) AS last_timestamp,
           MAX(received_at) AS last_received_at
    FROM telemetry
"""


def list_devices() -> list[dict]:
    connection = get_connection()
    rows = connection.execute(
        _DEVICE_SELECT + " GROUP BY device_id ORDER BY device_id"
    ).fetchall()
    connection.close()
    return [dict(row) for row in rows]


def get_device_summary(device_id: str) -> dict | None:
    connection = get_connection()
    row = connection.execute(
        _DEVICE_SELECT + " WHERE device_id = ? GROUP BY device_id", (device_id,)
    ).fetchone()
    if row is None:
        connection.close()
        return None

    spaces = connection.execute(
        "SELECT DISTINCT space_id FROM telemetry WHERE device_id = ? ORDER BY space_id",
        (device_id,),
    ).fetchall()
    connection.close()

    summary = dict(row)
    summary["spaces"] = [s["space_id"] for s in spaces]
    return summary
