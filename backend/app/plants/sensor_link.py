"""
plants/sensor_link.py

Resuelve que driver de sensor usar para una planta dada: si la planta
tiene un Sensor asignado (plant.sensor_id), se usa ese; si no, se cae al
sensor por defecto (SENSOR_MODE/DRACAL_SERIAL), igual que antes de que
existiera el registro de sensores multiples.
"""
from sqlalchemy.orm import Session

from app import models
from app.sensor import get_sensor, get_sensor_for
from app.sensor.base import SensorInterface


def resolve_sensor(plant: "models.Plant | None", db: Session) -> SensorInterface:
    if plant is not None and plant.sensor_id is not None:
        sensor_row = (
            db.query(models.Sensor).filter(models.Sensor.id == plant.sensor_id).first()
        )
        if sensor_row is not None:
            return get_sensor_for(sensor_row)
    return get_sensor()
