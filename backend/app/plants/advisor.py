"""
plants/advisor.py

/// <summary>
/// Logica de dominio que traduce una lectura ambiental (temperatura,
/// humedad relativa) y el perfil de una planta en una recomendacion de
/// riego: si debe regarse, por que, y cuantos litros aplicar segun la
/// capacidad de la maceta.
/// </summary>
///
/// Nota de honestidad tecnica: el Dracal VCP-PTH450-CAL mide humedad
/// relativa del AIRE, no humedad del sustrato/tierra. Este modulo usa la
/// humedad ambiente como una senal indirecta (proxy), combinada con el
/// tiempo transcurrido desde el ultimo riego, para estimar cuando regar.
/// Para una medicion directa de humedad de sustrato se recomendaria sumar
/// un sensor capacitivo de suelo; queda fuera del alcance de esta
/// asignacion, que exige especificamente el sensor Dracal PTH.
"""
from datetime import datetime, timezone

from app.models import Plant
from app.schemas import WateringAdvice
from app.sensor.base import SensorReading

HOURS_WITHOUT_WATER_ALERT = 48  # a partir de aqui, se sugiere regar igual


def _humidity_status(reading: SensorReading, plant: Plant) -> str:
    if reading.humidity_pct < plant.ideal_humidity_min:
        return "bajo"
    if reading.humidity_pct > plant.ideal_humidity_max:
        return "alto"
    return "optimo"


def build_watering_advice(reading: SensorReading, plant: Plant) -> WateringAdvice:
    status = _humidity_status(reading, plant)
    hours_since_watered = None
    if plant.last_watered_at is not None:
        last = plant.last_watered_at
        if last.tzinfo is None:
            last = last.replace(tzinfo=timezone.utc)
        hours_since_watered = (
            datetime.now(timezone.utc) - last
        ).total_seconds() / 3600.0

    should_water = False
    reasons = []

    if status == "bajo":
        should_water = True
        reasons.append(
            f"Humedad ambiente {reading.humidity_pct}% por debajo del rango "
            f"ideal ({plant.ideal_humidity_min}-{plant.ideal_humidity_max}%) "
            f"para {plant.species}."
        )

    if hours_since_watered is None:
        should_water = True
        reasons.append("No hay registro de riego previo para esta planta.")
    elif hours_since_watered >= HOURS_WITHOUT_WATER_ALERT:
        should_water = True
        reasons.append(
            f"Han pasado {hours_since_watered:.0f}h desde el ultimo riego "
            f"(limite recomendado: {HOURS_WITHOUT_WATER_ALERT}h)."
        )

    if reading.temperature_c > plant.ideal_temp_max:
        reasons.append(
            f"Temperatura {reading.temperature_c}C por encima del rango "
            f"ideal ({plant.ideal_temp_min}-{plant.ideal_temp_max}C): "
            "la planta pierde agua mas rapido por evapotranspiracion."
        )

    if not reasons:
        reasons.append(
            f"Condiciones dentro de rango para {plant.species}. No es "
            "necesario regar todavia."
        )

    recommended_liters = (
        round(plant.pot_volume_liters * plant.watering_fraction, 2)
        if should_water
        else 0.0
    )

    return WateringAdvice(
        should_water=should_water,
        reason=" ".join(reasons),
        recommended_liters=recommended_liters,
        humidity_status=status,
    )
