"""
tests/test_auto_save.py

Cubre app/jobs/auto_save.py: el job que el scheduler dispara cada
AUTO_SAVE_INTERVAL_MINUTES para guardar una lectura por cada planta
registrada, respetando el sensor que tenga asignada (resolve_sensor).

Los tests de "guardado duplicado omitido" y "listar plantas falla" son
el ciclo TDD documentado en evidence/security-review.md (entrada sobre
el scheduler): se escribieron ANTES de que save_readings_for_all_plants
tuviera la salvaguarda contra duplicados.
"""
from datetime import datetime, timedelta, timezone

from app import models
from app.jobs import auto_save


def test_saves_reading_for_each_registered_plant(client, db_session):
    plant_a = client.post(
        "/plants", json={"name": "Papa A", "pot_volume_liters": 10}
    ).json()
    plant_b = client.post(
        "/plants", json={"name": "Papa B", "pot_volume_liters": 10}
    ).json()

    auto_save.save_readings_for_all_plants(db=db_session)

    readings = db_session.query(models.Reading).all()
    saved_plant_ids = {r.plant_id for r in readings}
    assert saved_plant_ids == {plant_a["id"], plant_b["id"]}


def test_respects_assigned_sensor(client, db_session, monkeypatch):
    sensor = client.post(
        "/sensors", json={"name": "Dracal maceta auto", "serial": "E88801", "mode": "mock"}
    ).json()
    plant = client.post(
        "/plants",
        json={"name": "Ajo auto", "pot_volume_liters": 10, "sensor_id": sensor["id"]},
    ).json()

    seen_plant_ids = []
    real_resolve_sensor = auto_save.resolve_sensor

    def spy_resolve_sensor(plant_arg, db_arg):
        seen_plant_ids.append(plant_arg.id if plant_arg else None)
        return real_resolve_sensor(plant_arg, db_arg)

    monkeypatch.setattr(auto_save, "resolve_sensor", spy_resolve_sensor)

    auto_save.save_readings_for_all_plants(db=db_session)

    assert seen_plant_ids == [plant["id"]]
    reading = db_session.query(models.Reading).filter_by(plant_id=plant["id"]).one()
    assert reading.plant_id == plant["id"]


def test_continues_when_one_plant_sensor_fails(client, db_session, monkeypatch):
    plant_ok = client.post(
        "/plants", json={"name": "Planta OK", "pot_volume_liters": 10}
    ).json()
    plant_bad = client.post(
        "/plants", json={"name": "Planta rota", "pot_volume_liters": 10}
    ).json()

    real_resolve_sensor = auto_save.resolve_sensor

    class _BrokenSensor:
        def read(self):
            raise RuntimeError("sensor desconectado")

    def flaky_resolve_sensor(plant_arg, db_arg):
        if plant_arg is not None and plant_arg.id == plant_bad["id"]:
            return _BrokenSensor()
        return real_resolve_sensor(plant_arg, db_arg)

    monkeypatch.setattr(auto_save, "resolve_sensor", flaky_resolve_sensor)

    auto_save.save_readings_for_all_plants(db=db_session)  # no debe propagar la excepcion

    readings = db_session.query(models.Reading).all()
    saved_plant_ids = {r.plant_id for r in readings}
    assert saved_plant_ids == {plant_ok["id"]}


def test_no_plants_registered_does_nothing(db_session):
    auto_save.save_readings_for_all_plants(db=db_session)
    assert db_session.query(models.Reading).count() == 0


def test_skips_duplicate_run_within_guard_window(client, db_session, monkeypatch):
    """
    Simula dos schedulers/procesos disparando el job casi al mismo tiempo
    (por ejemplo, la ventana de reinicio de `uvicorn --reload`, o un
    despliegue accidental con varios workers): la segunda corrida no debe
    crear una segunda Reading para la misma planta.
    """
    monkeypatch.setenv("AUTO_SAVE_INTERVAL_MINUTES", "10")
    plant = client.post(
        "/plants", json={"name": "Papa duplicada", "pot_volume_liters": 10}
    ).json()

    auto_save.save_readings_for_all_plants(db=db_session)
    auto_save.save_readings_for_all_plants(db=db_session)

    readings = db_session.query(models.Reading).filter_by(plant_id=plant["id"]).all()
    assert len(readings) == 1


def test_does_not_skip_when_last_reading_is_older_than_guard_window(client, db_session, monkeypatch):
    monkeypatch.setenv("AUTO_SAVE_INTERVAL_MINUTES", "10")
    plant = client.post(
        "/plants", json={"name": "Papa con historial viejo", "pot_volume_liters": 10}
    ).json()
    old_reading = models.Reading(
        plant_id=plant["id"],
        temperature_c=20.0,
        humidity_pct=50.0,
        pressure_hpa=1000.0,
        timestamp=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db_session.add(old_reading)
    db_session.commit()

    auto_save.save_readings_for_all_plants(db=db_session)

    readings = db_session.query(models.Reading).filter_by(plant_id=plant["id"]).all()
    assert len(readings) == 2


def test_listing_plants_failure_is_contained_and_logged(db_session, monkeypatch):
    """
    Si la consulta inicial de plantas falla (por ejemplo 'database is
    locked' por otro proceso escribiendo al mismo tiempo), la funcion no
    debe propagar la excepcion.
    """

    def _boom(*args, **kwargs):
        raise RuntimeError("database is locked")

    monkeypatch.setattr(db_session, "query", _boom)

    auto_save.save_readings_for_all_plants(db=db_session)  # no debe lanzar
