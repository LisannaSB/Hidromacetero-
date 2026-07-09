r"""
sensor/dracal_pth.py

/// <summary>
/// Driver real para el sensor Dracal VCP-PTH450-CAL. Invoca la herramienta
/// oficial de linea de comandos 'dracal-usb-get' (incluida con DracalView,
/// ver https://www.dracal.com) y parsea su salida CSV.
/// </summary>
///
/// Canales del VCP-PTH450-CAL (confirmados via 'dracal-usb-get -l'):
///   Channel 0 -> MS5611 Pressure           (se pide en hPa via '-P hPa')
///   Channel 1 -> SHT31 Temperature         (C por defecto)
///   Channel 2 -> SHT31 Relative Humidity   (%)
///
/// Requisitos previos (ver README.md -> "Conectar el hardware real"):
///   1. Instalar DracalView (https://www.dracal.com) para obtener el
///      binario 'dracal-usb-get'.
///   2. Configurar DRACAL_BINARY con la ruta completa al ejecutable si no
///      esta en el PATH del sistema, por ejemplo en Windows:
///      DRACAL_BINARY=C:\Program Files (x86)\DracalView\dracal-usb-get.exe
///   3. Conectar el VCP-PTH450-CAL por USB. Su serial (ver etiqueta del
///      sensor) se pasa por variable de entorno DRACAL_SERIAL.
"""
import os
import subprocess

from app.sensor.base import SensorInterface, SensorReading

DRACAL_BINARY = os.environ.get("DRACAL_BINARY", "dracal-usb-get")
DEFAULT_TIMEOUT_S = 3.0


class DracalPTHSensorError(RuntimeError):
    """Se lanza cuando el binario dracal-usb-get falla o no esta disponible."""


class DracalPTHSensor(SensorInterface):
    """
    Driver real del Dracal VCP-PTH450-CAL.

    Se pide la presion directamente en hPa con '-P hPa' (en vez de leerla
    en kPa, la unidad por defecto, y convertirla a mano), para evitar
    depender de que la unidad por defecto de dracal-usb-get no cambie
    entre versiones.

    Ejemplo:
        dracal-usb-get -s E25876 -i 0,1,2 -P hPa -x 2
        -> "1013.20, 24.11, 46.80"   (hPa, C, %)
    """

    def __init__(self, serial: str | None = None) -> None:
        self.serial = serial or os.environ.get("DRACAL_SERIAL", "E25876")

    @property
    def is_mock(self) -> bool:
        return False

    def read(self) -> SensorReading:
        cmd = [
            DRACAL_BINARY,
            "-s",
            self.serial,
            "-i",
            "0,1,2",
            "-P",
            "hPa",
            "-x",
            "2",
        ]
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=DEFAULT_TIMEOUT_S,
                check=True,
            )
        except FileNotFoundError as exc:
            raise DracalPTHSensorError(
                f"No se encontro el binario '{DRACAL_BINARY}'. Instala "
                "DracalView y configura DRACAL_BINARY con la ruta completa "
                "al ejecutable, o usa el modo mock."
            ) from exc
        except subprocess.CalledProcessError as exc:
            raise DracalPTHSensorError(
                f"dracal-usb-get fallo (serial={self.serial}): {exc.stderr}"
            ) from exc
        except subprocess.TimeoutExpired as exc:
            raise DracalPTHSensorError(
                f"dracal-usb-get no respondio en {DEFAULT_TIMEOUT_S}s "
                f"(serial={self.serial})."
            ) from exc

        return self._parse(result.stdout)

    @staticmethod
    def _parse(raw_output: str) -> SensorReading:
        parts = [p.strip() for p in raw_output.strip().split(",")]
        if len(parts) != 3:
            raise DracalPTHSensorError(
                f"Salida inesperada de dracal-usb-get: '{raw_output}'"
            )
        pressure_hpa, temperature_c, humidity_pct = (float(p) for p in parts)
        return SensorReading(
            temperature_c=round(temperature_c, 2),
            humidity_pct=round(humidity_pct, 2),
            pressure_hpa=round(pressure_hpa, 2),
        )
