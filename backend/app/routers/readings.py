"""
routers/readings.py

Implementa los 3 casos de uso EXACTOS exigidos por la asignacion
(ver asignacion_react_fastapi.docx, seccion 2):

  1. GET  /readings/current      -> lectura actual del sensor Dracal
  2. POST /readings              -> persistir una lectura con timestamp
  3. GET  /readings?from=&to=    -> historial filtrado por rango de tiempo
"""
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.plants.advisor import build_watering_advice
from app.plants.sensor_link import resolve_sensor
from app.sensor.base import SensorReading
from app.sensor.dracal_pth import DracalPTHSensorError

router = APIRouter(prefix="/readings", tags=["readings"])


def _read_or_503(sensor):
    """
    Envuelve sensor.read() para que una falla de hardware real (binario
    no encontrado, sensor desconectado, timeout) se traduzca en un 503
    con un mensaje util, en vez de un 500 generico sin contexto.
    """
    try:
        return sensor.read()
    except DracalPTHSensorError as exc:
        raise HTTPException(
            status_code=503,
            detail=f"El sensor asignado no respondio: {exc}",
        )


@router.get("/current", response_model=schemas.CurrentReadingOut)
def get_current_reading(
    plant_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Caso de uso 1: Capturar lectura actual del sensor.
    Retorna la lectura en tiempo real (temperatura, humedad, presion) y,
    si se indica plant_id, la recomendacion de riego derivada. Si la
    planta tiene un sensor asignado (ver /sensors), se lee ese sensor en
    particular; si no, se usa el sensor por defecto.
    """
    plant = None
    if plant_id is not None:
        plant = db.query(models.Plant).filter(models.Plant.id == plant_id).first()
        if plant is None:
            raise HTTPException(status_code=404, detail="Planta no encontrada")

    sensor = resolve_sensor(plant, db)
    reading = _read_or_503(sensor)

    advice = None
    if plant is not None:
        advice = build_watering_advice(reading, plant)

    return schemas.CurrentReadingOut(
        id=0,
        plant_id=plant.id if plant else None,
        temperature_c=reading.temperature_c,
        humidity_pct=reading.humidity_pct,
        pressure_hpa=reading.pressure_hpa,
        timestamp=datetime.now(timezone.utc),
        advice=advice,
    )


@router.post("", response_model=schemas.ReadingOut, status_code=201)
def create_reading(payload: schemas.ReadingCreate, db: Session = Depends(get_db)):
    """
    Caso de uso 2: Guardar lectura en historial.
    Si no se envian valores explicitos, se toman del sensor asignado a la
    planta (o del sensor por defecto si no tiene uno asignado).
    """
    plant = None
    if payload.plant_id is not None:
        plant = (
            db.query(models.Plant).filter(models.Plant.id == payload.plant_id).first()
        )
        if plant is None:
            raise HTTPException(status_code=404, detail="Planta no encontrada")

    if payload.temperature_c is None or payload.humidity_pct is None or payload.pressure_hpa is None:
        live = _read_or_503(resolve_sensor(plant, db))
    else:
        live = SensorReading(
            temperature_c=payload.temperature_c,
            humidity_pct=payload.humidity_pct,
            pressure_hpa=payload.pressure_hpa,
        )

    reading = models.Reading(
        plant_id=payload.plant_id,
        temperature_c=payload.temperature_c
        if payload.temperature_c is not None
        else live.temperature_c,
        humidity_pct=payload.humidity_pct
        if payload.humidity_pct is not None
        else live.humidity_pct,
        pressure_hpa=payload.pressure_hpa
        if payload.pressure_hpa is not None
        else live.pressure_hpa,
    )
    db.add(reading)
    db.commit()
    db.refresh(reading)
    return reading


@router.get("", response_model=list[schemas.ReadingOut])
def list_readings(
    from_: Optional[datetime] = Query(default=None, alias="from"),
    to: Optional[datetime] = Query(default=None),
    plant_id: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
):
    """
    Caso de uso 3: Consultar historial por rango de tiempo.
    Ejemplo: GET /readings?from=2026-07-01T00:00:00&to=2026-07-07T23:59:59
    """
    query = db.query(models.Reading)
    if plant_id is not None:
        query = query.filter(models.Reading.plant_id == plant_id)
    if from_ is not None:
        query = query.filter(models.Reading.timestamp >= from_)
    if to is not None:
        query = query.filter(models.Reading.timestamp <= to)

    return query.order_by(models.Reading.timestamp.asc()).all()
