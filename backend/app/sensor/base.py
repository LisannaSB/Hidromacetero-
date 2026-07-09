"""
sensor/base.py

/// <summary>
/// Interfaz abstracta que todo driver de sensor ambiental debe implementar.
/// Permite intercambiar el sensor Dracal real por un mock sin tocar el
/// resto de la aplicacion (backend/app/routers/readings.py).
/// </summary>
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class SensorReading:
    temperature_c: float
    humidity_pct: float
    pressure_hpa: float


class SensorInterface(ABC):
    """Contrato minimo que cualquier sensor ambiental debe cumplir."""

    @abstractmethod
    def read(self) -> SensorReading:
        """Devuelve una lectura instantanea del sensor."""
        raise NotImplementedError

    @property
    @abstractmethod
    def is_mock(self) -> bool:
        raise NotImplementedError
