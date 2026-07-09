"""
models.py
Modelos SQLAlchemy del dominio HidroMacetero.

/// <summary>
/// Reading representa una lectura puntual del sensor Dracal VCP-PTH450-CAL
/// (temperatura, humedad relativa y presion atmosferica), asociada
/// opcionalmente a una maceta/planta monitoreada.
/// </summary>
"""
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Sensor(Base):
    """
    /// <summary>
    /// Registro de un sensor Dracal PTH fisico (o mock) disponible para
    /// asignar a una o mas plantas. Guarda el numero de serie (necesario
    /// para hablarle al hardware real via dracal-usb-get -s <serial>) y
    /// el ultimo resultado conocido de la verificacion de conexion.
    /// </summary>
    """

    __tablename__ = "sensors"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    serial = Column(String, nullable=False, unique=True, index=True)
    mode = Column(String, nullable=False, default="mock")  # "mock" | "real"
    created_at = Column(DateTime, default=utcnow)
    last_verified_at = Column(DateTime, nullable=True)
    last_status = Column(String, nullable=True)  # "ok" | "error" | None (nunca verificado)
    last_error = Column(String, nullable=True)

    plants = relationship("Plant", back_populates="sensor")


class Plant(Base):
    """
    /// <summary>
    /// Perfil de una planta/maceta monitoreada. Define los rangos de
    /// humedad ambiente ideales y la capacidad de la maceta en litros,
    /// usados para calcular la recomendacion de riego. Puede tener un
    /// Sensor fisico asignado; si no tiene ninguno, se usa el sensor por
    /// defecto configurado via SENSOR_MODE/DRACAL_SERIAL.
    /// </summary>
    """

    __tablename__ = "plants"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    species = Column(String, nullable=False, default="Solanum tuberosum (papa)")
    pot_volume_liters = Column(Float, nullable=False, default=10.0)
    ideal_humidity_min = Column(Float, nullable=False, default=60.0)
    ideal_humidity_max = Column(Float, nullable=False, default=80.0)
    ideal_temp_min = Column(Float, nullable=False, default=15.0)
    ideal_temp_max = Column(Float, nullable=False, default=24.0)
    watering_fraction = Column(Float, nullable=False, default=0.12)
    sensor_id = Column(Integer, ForeignKey("sensors.id"), nullable=True)
    last_watered_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)

    readings = relationship("Reading", back_populates="plant")
    sensor = relationship("Sensor", back_populates="plants")


class Reading(Base):
    """
    /// <summary>
    /// Lectura persistida del sensor Dracal PTH. Cada lectura queda
    /// asociada a una planta (macetero) y a un timestamp UTC.
    /// </summary>
    """

    __tablename__ = "readings"

    id = Column(Integer, primary_key=True, index=True)
    plant_id = Column(Integer, ForeignKey("plants.id"), nullable=True)
    temperature_c = Column(Float, nullable=False)
    humidity_pct = Column(Float, nullable=False)
    pressure_hpa = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=utcnow, index=True)

    plant = relationship("Plant", back_populates="readings")


class IrrigationEvent(Base):
    """
    /// <summary>
    /// Registro de un evento de riego (real o simulado) ejecutado por el
    /// driver del motor/bomba, incluyendo los litros dispensados y la
    /// duracion de activacion calculada.
    /// </summary>
    """

    __tablename__ = "irrigation_events"

    id = Column(Integer, primary_key=True, index=True)
    plant_id = Column(Integer, ForeignKey("plants.id"), nullable=True)
    liters_dispensed = Column(Float, nullable=False)
    duration_seconds = Column(Float, nullable=False)
    simulated = Column(Integer, default=1)  # 1 = simulado, 0 = hardware real
    triggered_by = Column(String, default="manual")  # manual | reminder | schedule
    timestamp = Column(DateTime, default=utcnow)
