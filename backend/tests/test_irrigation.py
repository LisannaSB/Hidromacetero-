"""
tests/test_irrigation.py

Cubre el driver de riego simulado y el endpoint POST /irrigation/water.
"""
from app.irrigation.motor_driver import SimulatedPumpDriver


def test_simulated_pump_calculates_duration_from_flow_rate():
    driver = SimulatedPumpDriver(flow_rate_lps=0.1)
    result = driver.dispense(liters=2.0)

    assert result.liters_dispensed == 2.0
    assert result.duration_seconds == 20.0
    assert result.simulated is True


def test_simulated_pump_rejects_non_positive_liters():
    driver = SimulatedPumpDriver()
    try:
        driver.dispense(0)
        assert False, "Debia lanzar ValueError"
    except ValueError:
        pass


def test_water_plant_endpoint_creates_event_and_updates_last_watered(client):
    plant_resp = client.post(
        "/plants",
        json={"name": "Papa balcon", "pot_volume_liters": 8, "watering_fraction": 0.1},
    )
    plant_id = plant_resp.json()["id"]

    response = client.post(
        "/irrigation/water", json={"plant_id": plant_id, "triggered_by": "manual"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["liters_dispensed"] == 0.8  # 8L * 0.1
    assert body["simulated"] == 1

    plant_after = client.get(f"/plants/{plant_id}").json()
    assert plant_after["last_watered_at"] is not None


def test_water_plant_rejects_liters_above_pot_capacity(client):
    """
    Evidencia de la revision de seguridad (evidence/security-review.md):
    no se debe poder pedir regar mas litros de los que la maceta soporta.
    """
    plant_resp = client.post("/plants", json={"name": "Papa chica", "pot_volume_liters": 5})
    plant_id = plant_resp.json()["id"]

    response = client.post(
        "/irrigation/water", json={"plant_id": plant_id, "liters": 999}
    )
    assert response.status_code == 400
