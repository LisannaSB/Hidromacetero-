"""
sensor/__init__.py

/// <summary>
/// Factory de sensores. Expone dos formas de obtener un driver:
///   - get_sensor(): el sensor "por defecto" configurado via variables de
///     entorno (SENSOR_MODE/DRACAL_SERIAL). Se mantiene por compatibilidad
///     para plantas sin sensor asignado explicitamente.
///   - get_sensor_for(sensor_row): construye (y cachea) un driver para un
///     registro de la tabla `sensors`, permitiendo que cada planta hable
///     con su propio sensor fisico (o su propio mock independiente).
/// </summary>
"""
import os

from app.sensor.base import SensorInterface, SensorReading  # noqa: F401
from app.sensor.dracal_pth import DracalPTHSensor
from app.sensor.mock import MockDracalSensor

_default_sensor_instance: SensorInterface | None = None
_sensor_cache: dict[str, SensorInterface] = {}


def get_sensor() -> SensorInterface:
    """Sensor por defecto (usado cuando una planta no tiene sensor asignado)."""
    global _default_sensor_instance
    if _default_sensor_instance is not None:
        return _default_sensor_instance

    mode = os.environ.get("SENSOR_MODE", "mock").lower()
    if mode == "real":
        _default_sensor_instance = DracalPTHSensor()
    else:
        _default_sensor_instance = MockDracalSensor()
    return _default_sensor_instance


def get_sensor_for(sensor_row) -> SensorInterface:
    """
    Construye (o reutiliza) el driver correspondiente a un registro
    `models.Sensor`. Se cachea por SERIAL (no por id de fila): el serial
    es lo que identifica al sensor fisico de verdad, mientras que el id
    de SQLite puede reciclarse si se borra y se crea un sensor nuevo,
    lo que causaria que un sensor 'real' recien creado devuelva por
    error el driver cacheado de un sensor viejo con el mismo id.
    """
    cache_key = f"{sensor_row.mode}:{sensor_row.serial}"
    cached = _sensor_cache.get(cache_key)
    if cached is not None:
        return cached

    if sensor_row.mode == "real":
        instance: SensorInterface = DracalPTHSensor(serial=sensor_row.serial)
    else:
        # Seed determinista a partir del serial: cada sensor mock tiene su
        # propia variacion aleatoria, pero reproducible entre reinicios.
        seed = abs(hash(sensor_row.serial)) % (2**32)
        instance = MockDracalSensor(seed=seed)

    _sensor_cache[cache_key] = instance
    return instance


def reset_sensor() -> None:
    """Utilidad para tests: fuerza recrear el sensor por defecto."""
    global _default_sensor_instance
    _default_sensor_instance = None


def reset_sensor_cache() -> None:
    """Utilidad para tests: limpia el cache de sensores por-planta."""
    global _sensor_cache
    _sensor_cache = {}

