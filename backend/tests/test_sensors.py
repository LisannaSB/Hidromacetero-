"""
tests/test_sensors.py

Cubre el registro de sensores, la verificacion de conexion, y que una
planta con un sensor asignado efectivamente lea de ese sensor (no del
sensor por defecto).
"""


def test_create_sensor(client):
    response = client.post(
        "/sensors", json={"name": "Dracal balcon", "serial": "E25876", "mode": "mock"}
    )
    assert response.status_code == 201
    body = response.json()
    assert body["serial"] == "E25876"
    assert body["mode"] == "mock"
    assert body["last_status"] is None


def test_create_sensor_rejects_duplicate_serial(client):
    client.post("/sensors", json={"name": "Sensor A", "serial": "E11111", "mode": "mock"})
    response = client.post(
        "/sensors", json={"name": "Sensor B", "serial": "E11111", "mode": "mock"}
    )
    assert response.status_code == 400


def test_verify_sensor_mock_reports_ok(client):
    created = client.post(
        "/sensors", json={"name": "Dracal cocina", "serial": "E22222", "mode": "mock"}
    ).json()

    response = client.post(f"/sensors/{created['id']}/verify")
    assert response.status_code == 200
    body = response.json()
    assert body["last_status"] == "ok"
    assert body["last_verified_at"] is not None


def test_verify_sensor_real_without_hardware_reports_error(client):
    """
    Un sensor marcado como 'real' sin el binario dracal-usb-get disponible
    debe reportar last_status='error', no tumbar la API.
    """
    created = client.post(
        "/sensors", json={"name": "Dracal real inexistente", "serial": "E99999", "mode": "real"}
    ).json()

    response = client.post(f"/sensors/{created['id']}/verify")
    assert response.status_code == 200
    body = response.json()
    assert body["last_status"] == "error"
    assert body["last_error"] is not None


def test_assign_sensor_to_plant_and_read_from_it(client):
    sensor = client.post(
        "/sensors", json={"name": "Dracal maceta 1", "serial": "E33333", "mode": "mock"}
    ).json()

    plant = client.post(
        "/plants",
        json={"name": "Ajo cocina", "pot_volume_liters": 15, "sensor_id": sensor["id"]},
    ).json()
    assert plant["sensor_id"] == sensor["id"]

    reading = client.get(f"/readings/current?plant_id={plant['id']}").json()
    assert reading["advice"] is not None  # confirma que se resolvio la planta y el sensor


def test_reassign_sensor_via_patch(client):
    sensor_a = client.post(
        "/sensors", json={"name": "Sensor A", "serial": "E44444", "mode": "mock"}
    ).json()
    sensor_b = client.post(
        "/sensors", json={"name": "Sensor B", "serial": "E55555", "mode": "mock"}
    ).json()
    plant = client.post(
        "/plants", json={"name": "Culantro", "pot_volume_liters": 10, "sensor_id": sensor_a["id"]}
    ).json()

    response = client.patch(f"/plants/{plant['id']}/sensor", json={"sensor_id": sensor_b["id"]})
    assert response.status_code == 200
    assert response.json()["sensor_id"] == sensor_b["id"]

    unassign = client.patch(f"/plants/{plant['id']}/sensor", json={"sensor_id": None})
    assert unassign.json()["sensor_id"] is None


def test_reading_with_broken_real_sensor_returns_clean_503(client):
    """
    Si a una planta se le asigna un sensor 'real' pero el hardware/binario
    no esta disponible, la API debe responder 503 con un mensaje claro,
    no un 500 generico sin contexto.
    """
    sensor = client.post(
        "/sensors", json={"name": "Dracal roto", "serial": "E77777", "mode": "real"}
    ).json()
    plant = client.post(
        "/plants", json={"name": "Planta con sensor roto", "pot_volume_liters": 10, "sensor_id": sensor["id"]}
    ).json()

    response = client.get(f"/readings/current?plant_id={plant['id']}")
    assert response.status_code == 503
    assert "sensor" in response.json()["detail"].lower()


def test_create_plant_with_nonexistent_sensor_returns_404(client):
    response = client.post(
        "/plants", json={"name": "Planta X", "pot_volume_liters": 10, "sensor_id": 9999}
    )
    assert response.status_code == 404


def test_delete_sensor_in_use_is_blocked(client):
    sensor = client.post(
        "/sensors", json={"name": "Sensor en uso", "serial": "E66666", "mode": "mock"}
    ).json()
    client.post(
        "/plants", json={"name": "Planta con sensor", "pot_volume_liters": 10, "sensor_id": sensor["id"]}
    )

    response = client.delete(f"/sensors/{sensor['id']}")
    assert response.status_code == 400
