"""Pruebas automáticas de la Guía 4 (consultas REST).

Cada prueba usa una base SQLite TEMPORAL con datos sembrados aquí mismo,
así no dependen del parking.db real ni de datos cargados a mano.
"""
import pytest
from fastapi.testclient import TestClient

from backend import database
from backend.main import app


def _message(device_id, space_id, sequence, ts, occupied=True, duration=10.0):
    return {
        "message_id": f"{device_id}-{space_id}-{sequence:06d}",
        "device_id": device_id,
        "timestamp": ts,
        "sequence": sequence,
        "measurements": {
            "space_id": space_id,
            "occupied": occupied,
            "distance": 12.5,
            "parking_duration": duration,
        },
    }


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "DB_PATH", str(tmp_path / "test.db"))
    database.init_database()

    # 12 lecturas de PARK-001 (dos espacios) el 2026-10-19 y 3 de PARK-002.
    for seq in range(1, 7):
        for space in ("E01", "E02"):
            database.save_telemetry(
                _message("PARK-001", space, seq, f"2026-10-19T10:0{seq}:00+00:00")
            )
    for seq in range(1, 4):
        database.save_telemetry(
            _message("PARK-002", "A01", seq, f"2026-10-20T08:0{seq}:00+00:00")
        )

    with TestClient(app) as test_client:
        yield test_client


# ---- Los 5 casos mínimos de la guía ----

def test_measurements_returns_200_and_json_list(client):
    response = client.get("/api/measurements")
    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, list) and len(body) > 0
    assert {"device_id", "sequence", "measurements", "message_id"} <= body[0].keys()
    assert isinstance(body[0]["measurements"], dict)  # objeto, no texto JSON


def test_limit_restricts_number_of_items(client):
    response = client.get("/api/measurements?limit=5")
    assert response.status_code == 200
    assert len(response.json()) == 5


def test_device_id_filters_correctly(client):
    response = client.get("/api/measurements?device_id=PARK-002&limit=100")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 3
    assert all(item["device_id"] == "PARK-002" for item in items)


def test_unknown_device_returns_404(client):
    response = client.get("/api/devices/NO-EXISTE")
    assert response.status_code == 404
    assert response.json()["detail"] == "Dispositivo no encontrado"


def test_invalid_limit_returns_422(client):
    assert client.get("/api/measurements?limit=0").status_code == 422
    assert client.get("/api/measurements?limit=500").status_code == 422


# ---- Casos adicionales ----

def test_negative_offset_returns_422(client):
    assert client.get("/api/measurements?offset=-1").status_code == 422


def test_offset_skips_rows(client):
    first = client.get("/api/measurements?limit=5&offset=0").json()
    second = client.get("/api/measurements?limit=5&offset=5").json()
    assert {i["id"] for i in first}.isdisjoint({i["id"] for i in second})


def test_results_are_newest_first(client):
    ids = [i["id"] for i in client.get("/api/measurements?limit=100").json()]
    assert ids == sorted(ids, reverse=True)


def test_no_matches_returns_200_and_empty_list(client):
    response = client.get("/api/measurements?device_id=SIN-DATOS")
    assert response.status_code == 200
    assert response.json() == []


def test_devices_list(client):
    response = client.get("/api/devices")
    assert response.status_code == 200
    by_id = {d["device_id"]: d for d in response.json()}
    assert by_id["PARK-001"]["measurement_count"] == 12
    assert by_id["PARK-001"]["space_count"] == 2
    assert by_id["PARK-002"]["measurement_count"] == 3


def test_existing_device_returns_200(client):
    response = client.get("/api/devices/PARK-001")
    assert response.status_code == 200
    assert response.json()["spaces"] == ["E01", "E02"]


def test_filter_by_space(client):
    items = client.get("/api/measurements?device_id=PARK-001&space_id=E02&limit=100").json()
    assert len(items) == 6
    assert all(i["measurements"]["space_id"] == "E02" for i in items)


def test_time_range_filter(client):
    url = ("/api/measurements?device_id=PARK-001&limit=100"
           "&from=2026-10-19T10:03:00Z&to=2026-10-19T10:05:00Z")
    items = client.get(url).json()
    assert len(items) == 6  # secuencias 3, 4 y 5 en dos espacios
    assert {i["sequence"] for i in items} == {3, 4, 5}


def test_invalid_date_returns_422(client):
    assert client.get("/api/measurements?from=ayer").status_code == 422


def test_unknown_route_returns_404(client):
    assert client.get("/api/no-existe").status_code == 404


# ---- La Guía 3 sigue funcionando ----

def test_post_telemetry_still_returns_201_and_is_queryable(client):
    msg = _message("PARK-003", "Z01", 1, "2026-10-21T09:00:00Z")
    assert client.post("/api/telemetry", json=msg).status_code == 201
    items = client.get("/api/measurements?device_id=PARK-003").json()
    assert items[0]["message_id"] == "PARK-003-Z01-000001"


def test_post_invalid_telemetry_is_rejected(client):
    bad = _message("PARK-003", "Z01", 1, "2026-10-21T09:00:00Z")
    bad["measurements"]["distance"] = "lejos"
    assert client.post("/api/telemetry", json=bad).status_code == 422


def test_old_v1_routes_for_dashboard_still_work(client):
    for path in ("/api/v1/parking", "/api/v1/history", "/api/v1/alerts"):
        assert client.get(path).status_code == 200
