"""
routers/sensors.py

Endpoints para administrar el catalogo de sensores Dracal disponibles:
registrarlos (con su numero de serie), listarlos para asignarlos a una
planta, y verificar que realmente responden antes de confiar en ellos.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.sensor import get_sensor_for
from app.sensor.dracal_pth import DracalPTHSensorError

router = APIRouter(prefix="/sensors", tags=["sensors"])


@router.post("", response_model=schemas.SensorOut, status_code=201)
def create_sensor(payload: schemas.SensorCreate, db: Session = Depends(get_db)):
    sensor = models.Sensor(name=payload.name, serial=payload.serial, mode=payload.mode)
    db.add(sensor)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un sensor registrado con el serial '{payload.serial}'.",
        )
    db.refresh(sensor)
    return sensor


@router.get("", response_model=list[schemas.SensorOut])
def list_sensors(db: Session = Depends(get_db)):
    return db.query(models.Sensor).order_by(models.Sensor.id.asc()).all()


@router.get("/{sensor_id}", response_model=schemas.SensorOut)
def get_sensor_detail(sensor_id: int, db: Session = Depends(get_db)):
    sensor = db.query(models.Sensor).filter(models.Sensor.id == sensor_id).first()
    if sensor is None:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")
    return sensor


@router.post("/{sensor_id}/verify", response_model=schemas.SensorOut)
def verify_sensor(sensor_id: int, db: Session = Depends(get_db)):
    """
    Intenta leer del sensor ahora mismo (real o mock, segun su 'mode') y
    guarda el resultado. Para un sensor 'real' esto realmente invoca
    dracal-usb-get con el serial configurado -- es la forma de confirmar
    que el hardware esta conectado y responde antes de asignarlo a una
    planta.
    """
    sensor = db.query(models.Sensor).filter(models.Sensor.id == sensor_id).first()
    if sensor is None:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")

    driver = get_sensor_for(sensor)
    try:
        driver.read()
        sensor.last_status = "ok"
        sensor.last_error = None
    except DracalPTHSensorError as exc:
        sensor.last_status = "error"
        sensor.last_error = str(exc)
    except Exception as exc:  # salvaguarda: nunca dejar caer la API por un driver
        sensor.last_status = "error"
        sensor.last_error = f"Error inesperado: {exc}"

    sensor.last_verified_at = datetime.now(timezone.utc)
    db.add(sensor)
    db.commit()
    db.refresh(sensor)
    return sensor


@router.delete("/{sensor_id}", status_code=204)
def delete_sensor(sensor_id: int, db: Session = Depends(get_db)):
    sensor = db.query(models.Sensor).filter(models.Sensor.id == sensor_id).first()
    if sensor is None:
        raise HTTPException(status_code=404, detail="Sensor no encontrado")

    in_use = db.query(models.Plant).filter(models.Plant.sensor_id == sensor_id).count()
    if in_use > 0:
        raise HTTPException(
            status_code=400,
            detail=(
                f"No se puede eliminar: {in_use} planta(s) tienen este sensor "
                "asignado. Reasignalas primero."
            ),
        )

    db.delete(sensor)
    db.commit()
    return None
