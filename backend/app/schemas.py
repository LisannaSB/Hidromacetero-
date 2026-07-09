"""
schemas.py
Esquemas Pydantic (request/response) para la API de HidroMacetero.
"""
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# ---------- Sensor ----------

class SensorCreate(BaseModel):
    name: str = Field(..., examples=["Dracal balcon"])
    serial: str = Field(..., examples=["E25876"])
    mode: Literal["mock", "real"] = Field(
        default="mock",
        description="'mock' para pruebas sin hardware, 'real' para el Dracal fisico.",
    )


class SensorOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    serial: str
    mode: str
    created_at: datetime
    last_verified_at: Optional[datetime] = None
    last_status: Optional[str] = None
    last_error: Optional[str] = None


# ---------- Plant ----------

class PlantBase(BaseModel):
    name: str = Field(..., examples=["Macetero balcon - Papa criolla"])
    species: str = Field(default="Solanum tuberosum (papa)")
    pot_volume_liters: float = Field(..., gt=0, examples=[10.0])
    ideal_humidity_min: float = Field(default=60.0, ge=0, le=100)
    ideal_humidity_max: float = Field(default=80.0, ge=0, le=100)
    ideal_temp_min: float = Field(default=15.0)
    ideal_temp_max: float = Field(default=24.0)
    watering_fraction: float = Field(
        default=0.12,
        gt=0,
        lt=1,
        description="Fraccion del volumen de la maceta a regar por ciclo (0-1).",
    )
    sensor_id: Optional[int] = Field(
        default=None,
        description="Sensor Dracal asignado a esta planta. Si se omite, se usa el sensor por defecto (SENSOR_MODE/DRACAL_SERIAL).",
    )


class PlantCreate(PlantBase):
    pass


class PlantOut(PlantBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    last_watered_at: Optional[datetime] = None
    created_at: datetime


class PlantSensorAssign(BaseModel):
    sensor_id: Optional[int] = None


# ---------- Reading ----------

class ReadingCreate(BaseModel):
    plant_id: Optional[int] = None
    temperature_c: Optional[float] = Field(
        default=None, description="Si se omite, se toma la lectura actual del sensor."
    )
    humidity_pct: Optional[float] = None
    pressure_hpa: Optional[float] = None


class ReadingOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    plant_id: Optional[int]
    temperature_c: float
    humidity_pct: float
    pressure_hpa: float
    timestamp: datetime


class WateringAdvice(BaseModel):
    should_water: bool
    reason: str
    recommended_liters: float
    humidity_status: str  # "bajo" | "optimo" | "alto"


class CurrentReadingOut(ReadingOut):
    plant_id: Optional[int] = None
    advice: Optional[WateringAdvice] = None


class NextWateringEstimate(BaseModel):
    hours_since_last_watering: Optional[float]
    hours_until_recommended_watering: float


# ---------- Irrigation ----------

class IrrigationRequest(BaseModel):
    plant_id: int
    liters: Optional[float] = Field(
        default=None,
        gt=0,
        description="Si se omite, se calcula automaticamente segun el perfil de la planta.",
    )
    triggered_by: str = Field(default="manual")


class IrrigationEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    plant_id: Optional[int]
    liters_dispensed: float
    duration_seconds: float
    simulated: int
    triggered_by: str
    timestamp: datetime
