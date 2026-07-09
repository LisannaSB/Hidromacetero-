"""
tests/test_advisor.py

Pruebas unitarias de la logica de recomendacion de riego
(app/plants/advisor.py), independientes de la API HTTP.
"""
from datetime import datetime, timedelta, timezone

from app.models import Plant
from app.plants.advisor import build_watering_advice
from app.sensor.base import SensorReading


def make_plant(**overrides) -> Plant:
    base = dict(
        id=1,
        name="Papa criolla",
        species="Solanum tuberosum",
        pot_volume_liters=10.0,
        ideal_humidity_min=60.0,
        ideal_humidity_max=80.0,
        ideal_temp_min=15.0,
        ideal_temp_max=24.0,
        watering_fraction=0.12,
        last_watered_at=None,
    )
    base.update(overrides)
    return Plant(**base)


def test_low_humidity_triggers_watering():
    plant = make_plant(last_watered_at=datetime.now(timezone.utc))
    reading = SensorReading(temperature_c=20, humidity_pct=40, pressure_hpa=1013)

    advice = build_watering_advice(reading, plant)

    assert advice.should_water is True
    assert advice.humidity_status == "bajo"
    assert advice.recommended_liters == round(10.0 * 0.12, 2)


def test_optimal_conditions_recently_watered_do_not_trigger():
    plant = make_plant(last_watered_at=datetime.now(timezone.utc))
    reading = SensorReading(temperature_c=20, humidity_pct=70, pressure_hpa=1013)

    advice = build_watering_advice(reading, plant)

    assert advice.should_water is False
    assert advice.humidity_status == "optimo"
    assert advice.recommended_liters == 0.0


def test_no_previous_watering_record_triggers_watering():
    plant = make_plant(last_watered_at=None)
    reading = SensorReading(temperature_c=20, humidity_pct=70, pressure_hpa=1013)

    advice = build_watering_advice(reading, plant)

    assert advice.should_water is True


def test_long_time_since_last_watering_triggers_even_if_humid():
    old_date = datetime.now(timezone.utc) - timedelta(hours=72)
    plant = make_plant(last_watered_at=old_date)
    reading = SensorReading(temperature_c=20, humidity_pct=70, pressure_hpa=1013)

    advice = build_watering_advice(reading, plant)

    assert advice.should_water is True
    assert "72h" in advice.reason or "Han pasado" in advice.reason
