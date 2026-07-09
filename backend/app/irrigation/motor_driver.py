"""
irrigation/motor_driver.py

/// <summary>
/// Driver del sistema de riego automatizado. Abstrae una bomba/motor
/// (p. ej. controlada por un puente H tipo L298N o un modulo de rele)
/// detras de una interfaz comun, con una implementacion simulada por
/// defecto ya que no se cuenta con el hardware de riego fisico.
/// </summary>
///
/// Nota: igual que el sensor, el driver expone SIMULATED_MODE por defecto.
/// Para hardware real, reemplazar SimulatedPumpDriver por una
/// implementacion que hable GPIO (p. ej. via RPi.GPIO o gpiozero) con el
/// mismo contrato 'dispense(liters)'.
"""
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class IrrigationResult:
    liters_dispensed: float
    duration_seconds: float
    simulated: bool


class PumpDriverInterface(ABC):
    @abstractmethod
    def dispense(self, liters: float) -> IrrigationResult:
        raise NotImplementedError


class SimulatedPumpDriver(PumpDriverInterface):
    """
    Simula una bomba de 12V con caudal fijo (litros/segundo). Registra la
    accion por consola a modo de log de auditoria, tal como lo haria un
    driver real antes/despues de accionar el motor.
    """

    def __init__(self, flow_rate_lps: float = 0.05) -> None:
        # 0.05 L/s ~ 3 L/min, tipico de una micro-bomba sumergible de 12V.
        self.flow_rate_lps = flow_rate_lps

    def dispense(self, liters: float) -> IrrigationResult:
        if liters <= 0:
            raise ValueError("Los litros a dispensar deben ser > 0")

        duration_s = round(liters / self.flow_rate_lps, 2)

        print(
            f"[SimulatedPumpDriver] Activando motor de riego "
            f"por {duration_s}s para dispensar {liters}L "
            f"(caudal simulado: {self.flow_rate_lps} L/s)."
        )
        # En hardware real aqui iria, por ejemplo:
        #   GPIO.output(PUMP_RELAY_PIN, GPIO.HIGH)
        #   time.sleep(duration_s)
        #   GPIO.output(PUMP_RELAY_PIN, GPIO.LOW)
        # En la simulacion no bloqueamos con sleep real para no ralentizar
        # la API; solo se calcula el tiempo que tomaria.
        time.sleep(min(duration_s, 0.2))  # micro-pausa simbolica

        print("[SimulatedPumpDriver] Riego simulado completado.")

        return IrrigationResult(
            liters_dispensed=liters,
            duration_seconds=duration_s,
            simulated=True,
        )


_driver_instance: PumpDriverInterface | None = None


def get_pump_driver() -> PumpDriverInterface:
    global _driver_instance
    if _driver_instance is None:
        _driver_instance = SimulatedPumpDriver()
    return _driver_instance
