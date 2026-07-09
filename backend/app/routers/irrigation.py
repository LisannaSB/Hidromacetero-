"""
routers/irrigation.py

Endpoint de soporte para accionar el riego automatizado (simulado). No es
uno de los 3 casos de uso obligatorios de la asignacion, pero responde al
requerimiento adicional del usuario: simular un driver de motor/bomba
para riego, calculando litros y tiempo de actuacion.
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models, schemas
from app.database import get_db
from app.irrigation.motor_driver import get_pump_driver
from app.plants.advisor import build_watering_advice
from app.plants.sensor_link import resolve_sensor
from app.sensor.dracal_pth import DracalPTHSensorError

router = APIRouter(prefix="/irrigation", tags=["irrigation"])


@router.post("/water", response_model=schemas.IrrigationEventOut, status_code=201)
def water_plant(payload: schemas.IrrigationRequest, db: Session = Depends(get_db)):
    plant = db.query(models.Plant).filter(models.Plant.id == payload.plant_id).first()
    if plant is None:
        raise HTTPException(status_code=404, detail="Planta no encontrada")

    liters = payload.liters
    if liters is None:
        try:
            reading = resolve_sensor(plant, db).read()
        except DracalPTHSensorError as exc:
            raise HTTPException(
                status_code=503,
                detail=f"No se pudo leer el sensor para calcular los litros: {exc}",
            )
        advice = build_watering_advice(reading, plant)
        liters = advice.recommended_liters or round(
            plant.pot_volume_liters * plant.watering_fraction, 2
        )
    elif liters > plant.pot_volume_liters:
        # Hallazgo de la revision de seguridad (ver evidence/security-review.md):
        # sin este limite, un valor de 'liters' arbitrario en el request podia
        # activar el driver de riego (fisico a futuro) por un volumen mayor a
        # la capacidad real de la maceta.
        raise HTTPException(
            status_code=400,
            detail=(
                f"liters ({liters}) no puede superar la capacidad de la "
                f"maceta ({plant.pot_volume_liters} L)."
            ),
        )

    driver = get_pump_driver()
    result = driver.dispense(liters)

    event = models.IrrigationEvent(
        plant_id=plant.id,
        liters_dispensed=result.liters_dispensed,
        duration_seconds=result.duration_seconds,
        simulated=1 if result.simulated else 0,
        triggered_by=payload.triggered_by,
    )
    db.add(event)

    from datetime import datetime, timezone

    plant.last_watered_at = datetime.now(timezone.utc)
    db.add(plant)

    db.commit()
    db.refresh(event)
    return event


@router.get("/history/{plant_id}", response_model=list[schemas.IrrigationEventOut])
def irrigation_history(plant_id: int, db: Session = Depends(get_db)):
    return (
        db.query(models.IrrigationEvent)
        .filter(models.IrrigationEvent.plant_id == plant_id)
        .order_by(models.IrrigationEvent.timestamp.desc())
        .all()
    )
