"""
tests/test_watering_estimate.py

Evidencia real de TDD (ver evidence/tdd-cycle.md): este archivo se creo
ANTES de implementar el endpoint GET /plants/{id}/next-watering-estimate.
"""


def test_next_watering_estimate_returns_hours_remaining(client):
    plant_resp = client.post(
        "/plants",
        json={"name": "Papa TDD", "pot_volume_liters": 10},
    )
    plant_id = plant_resp.json()["id"]

    response = client.get(f"/plants/{plant_id}/next-watering-estimate")

    assert response.status_code == 200
    body = response.json()
    assert "hours_since_last_watering" in body
    assert "hours_until_recommended_watering" in body
    # Planta recien creada, nunca regada -> deberia recomendar regar ya (0h).
    assert body["hours_until_recommended_watering"] == 0
