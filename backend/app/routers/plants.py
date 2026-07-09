"""
routers/plants.py

Endpoints de soporte (fuera de los 3 casos de uso obligatorios) para
administrar perfiles de planta/maceta: nombre, especie, capacidad en
litros y rangos ideales de humedad/temperatura. Necesario para que el
calculo de riego (litros recomendados) tenga contexto real.
"""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.plants.advisor import HOURS_WITHOUT_WATER_ALERT

router = APIRouter(prefix="/plants", tags=["plants"])


@router.post("", response_model=schemas.PlantOut, status_code=201)
def create_plant(payload: schemas.PlantCreate, db: Session = Depends(get_db)):
    if payload.sensor_id is not None:
        sensor = db.query(models.Sensor).filter(models.Sensor.id == payload.sensor_id).first()
        if sensor is None:
            raise HTTPException(status_code=404, detail="Sensor no encontrado")

    plant = models.Plant(**payload.model_dump())
    db.add(plant)
    db.commit()
    db.refresh(plant)
    return plant


@router.patch("/{plant_id}/sensor", response_model=schemas.PlantOut)
def assign_sensor(
    plant_id: int, payload: schemas.PlantSensorAssign, db: Session = Depends(get_db)
):
    """
    Asigna (o quita, si sensor_id es null) el sensor fisico de una planta
    ya existente, sin tener que recrearla.
    """
    plant = db.query(models.Plant).filter(models.Plant.id == plant_id).first()
    if plant is None:
        raise HTTPException(status_code=404, detail="Planta no encontrada")

    if payload.sensor_id is not None:
        sensor = db.query(models.Sensor).filter(models.Sensor.id == payload.sensor_id).first()
        if sensor is None:
            raise HTTPException(status_code=404, detail="Sensor no encontrado")

    plant.sensor_id = payload.sensor_id
    db.add(plant)
    db.commit()
    db.refresh(plant)
    return plant


@router.get("", response_model=list[schemas.PlantOut])
def list_plants(db: Session = Depends(get_db)):
    return db.query(models.Plant).order_by(models.Plant.id.asc()).all()


@router.get("/{plant_id}", response_model=schemas.PlantOut)
def get_plant(plant_id: int, db: Session = Depends(get_db)):
    plant = db.query(models.Plant).filter(models.Plant.id == plant_id).first()
    if plant is None:
        raise HTTPException(status_code=404, detail="Planta no encontrada")
    return plant


@router.get(
    "/{plant_id}/next-watering-estimate",
    response_model=schemas.NextWateringEstimate,
)
def next_watering_estimate(plant_id: int, db: Session = Depends(get_db)):
    """
    Estima cuantas horas faltan para el proximo riego recomendado,
    basado unicamente en el tiempo transcurrido desde el ultimo riego
    (independiente de la lectura de humedad actual). Implementado como
    ciclo TDD de ejemplo: ver evidence/tdd-cycle.md.
    """
    plant = db.query(models.Plant).filter(models.Plant.id == plant_id).first()
    if plant is None:
        raise HTTPException(status_code=404, detail="Planta no encontrada")

    if plant.last_watered_at is None:
        return schemas.NextWateringEstimate(
            hours_since_last_watering=None,
            hours_until_recommended_watering=0.0,
        )

    last = plant.last_watered_at
    if last.tzinfo is None:
        last = last.replace(tzinfo=timezone.utc)

    hours_since = (datetime.now(timezone.utc) - last).total_seconds() / 3600.0
    hours_remaining = max(HOURS_WITHOUT_WATER_ALERT - hours_since, 0.0)

    return schemas.NextWateringEstimate(
        hours_since_last_watering=round(hours_since, 2),
        hours_until_recommended_watering=round(hours_remaining, 2),
    )
