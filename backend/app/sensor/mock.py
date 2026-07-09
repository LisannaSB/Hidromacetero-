"""
sensor/mock.py

/// <summary>
/// Implementacion simulada del sensor Dracal PTH. Genera lecturas
/// realistas con una leve caminata aleatoria alrededor de valores base,
/// para poder desarrollar y correr pytest sin el hardware conectado.
/// </summary>
"""
import random

from app.sensor.base import SensorInterface, SensorReading


class MockDracalSensor(SensorInterface):
    def __init__(
        self,
        base_temp_c: float = 24.0,
        base_humidity_pct: float = 55.0,
        base_pressure_hpa: float = 1013.0,
        seed: int | None = None,
    ) -> None:
        self._temp = base_temp_c
        self._humidity = base_humidity_pct
        self._pressure = base_pressure_hpa
        self._rng = random.Random(seed)

    @property
    def is_mock(self) -> bool:
        return True

    def read(self) -> SensorReading:
        # Caminata aleatoria acotada para simular variacion ambiental real.
        self._temp += self._rng.uniform(-0.3, 0.3)
        self._humidity += self._rng.uniform(-1.5, 1.5)
        self._pressure += self._rng.uniform(-0.4, 0.4)

        self._humidity = min(max(self._humidity, 20.0), 95.0)
        self._temp = min(max(self._temp, 10.0), 38.0)

        return SensorReading(
            temperature_c=round(self._temp, 2),
            humidity_pct=round(self._humidity, 2),
            pressure_hpa=round(self._pressure, 2),
        )
