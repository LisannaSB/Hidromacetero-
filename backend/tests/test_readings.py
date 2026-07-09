"""
tests/test_readings.py

Cubre los 3 casos de uso obligatorios de la asignacion:
  1. GET  /readings/current
  2. POST /readings
  3. GET  /readings?from=&to=

Este archivo tambien es el que se referencia en EVIDENCE.md para el
ciclo TDD del tema "Test-driven Iteration": test_create_reading_persists_values
fue el primero escrito ANTES de existir el endpoint (ver evidence/tdd-cycle.md).
"""
from datetime import datetime, timedelta


def test_get_current_reading_returns_sensor_values(client):
    response = client.get("/readings/current")
    assert response.status_code == 200
    body = response.json()
    assert "temperature_c" in body
    assert "humidity_pct" in body
    assert "pressure_hpa" in body
    assert 0 <= body["humidity_pct"] <= 100


def test_get_current_reading_with_plant_returns_advice(client):
    plant_resp = client.post(
        "/plants",
        json={
            "name": "Papa de prueba",
            "species": "Solanum tuberosum",
            "pot_volume_liters": 10,
            "ideal_humidity_min": 60,
            "ideal_humidity_max": 80,
        },
    )
    plant_id = plant_resp.json()["id"]

    response = client.get(f"/readings/current?plant_id={plant_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["advice"] is not None
    assert "should_water" in body["advice"]
    assert "recommended_liters" in body["advice"]


def test_get_current_reading_invalid_plant_returns_404(client):
    response = client.get("/readings/current?plant_id=9999")
    assert response.status_code == 404


def test_create_reading_persists_values(client):
    """
    Caso de uso 2. Este fue el test guia del ciclo TDD documentado en
    evidence/tdd-cycle.md: se escribio antes de implementar el endpoint
    POST /readings, fallo (404), y luego paso al implementarlo.
    """
    payload = {
        "temperature_c": 22.5,
        "humidity_pct": 65.0,
        "pressure_hpa": 1012.3,
    }
    response = client.post("/readings", json=payload)
    assert response.status_code == 201
    body = response.json()
    assert body["temperature_c"] == 22.5
    assert body["humidity_pct"] == 65.0
    assert body["pressure_hpa"] == 1012.3
    assert body["id"] is not None
    assert body["timestamp"] is not None


def test_create_reading_without_values_uses_live_sensor(client):
    response = client.post("/readings", json={})
    assert response.status_code == 201
    body = response.json()
    assert isinstance(body["temperature_c"], float)


def test_list_readings_filters_by_time_range(client):
    client.post("/readings", json={"temperature_c": 20, "humidity_pct": 50, "pressure_hpa": 1010})
    client.post("/readings", json={"temperature_c": 21, "humidity_pct": 55, "pressure_hpa": 1011})

    now = datetime.utcnow()
    past = (now - timedelta(days=1)).isoformat()
    future = (now + timedelta(days=1)).isoformat()

    response = client.get(f"/readings?from={past}&to={future}")
    assert response.status_code == 200
    body = response.json()
    assert len(body) >= 2

    far_future = (now + timedelta(days=10)).isoformat()
    far_future_end = (now + timedelta(days=20)).isoformat()
    empty_response = client.get(f"/readings?from={far_future}&to={far_future_end}")
    assert empty_response.json() == []
