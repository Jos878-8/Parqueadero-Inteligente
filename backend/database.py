import sqlite3

DATABASE = "parking.db"


def get_connection():
    connection = sqlite3.connect(DATABASE)
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
            parking_duration REAL NOT NULL
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            space_id TEXT NOT NULL,
            message TEXT NOT NULL,
            parking_duration REAL NOT NULL,
            timestamp TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()


def save_telemetry(data):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO telemetry (
            message_id,
            device_id,
            space_id,
            timestamp,
            sequence,
            occupied,
            distance,
            parking_duration
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        data.get("message_id"),
        data["device_id"],
        data["measurements"]["space_id"],
        data["timestamp"],
        data.get("sequence"),
        int(data["measurements"]["occupied"]),
        data["measurements"]["distance"],
        data["measurements"]["parking_duration"]
    ))

    connection.commit()
    connection.close()


def get_latest_telemetry():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT t.*
        FROM telemetry t
        INNER JOIN (
            SELECT space_id, MAX(id) AS max_id
            FROM telemetry
            GROUP BY space_id
        ) latest
        ON t.id = latest.max_id
        ORDER BY t.space_id
    """)

    rows = cursor.fetchall()
    connection.close()

    return [dict(row) for row in rows]


def get_history():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM telemetry
        ORDER BY id DESC
        LIMIT 100
    """)

    rows = cursor.fetchall()
    connection.close()

    return [dict(row) for row in rows]


def save_alert(space_id, message, parking_duration, timestamp):
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO alerts (
            space_id,
            message,
            parking_duration,
            timestamp
        )
        VALUES (?, ?, ?, ?)
    """, (
        space_id,
        message,
        parking_duration,
        timestamp
    ))

    connection.commit()
    connection.close()


def get_alerts():
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT *
        FROM alerts
        ORDER BY id DESC
        LIMIT 100
    """)

    rows = cursor.fetchall()
    connection.close()

    return [dict(row) for row in rows]