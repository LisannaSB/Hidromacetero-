"""
jobs/auto_save.py

/// <summary>
/// Job periodico de guardado automatico de lecturas. Reemplaza la
/// dependencia del boton manual "Guardar lectura actual": por cada
/// planta registrada, resuelve su sensor asignado (o el sensor por
/// defecto) via resolve_sensor y persiste una Reading. Un sensor que
/// falle para una planta no debe abortar el resto.
/// </summary>
///
/// Nota de robustez (ver evidence/security-review.md): esta funcion no
/// asume que solo hay un scheduler corriendo. El singleton en
/// scheduler.py evita duplicar el job DENTRO de un mismo proceso, pero
/// no protege contra dos procesos escribiendo a la vez (por ejemplo la
/// ventana de reinicio de `uvicorn --reload`, o un despliegue futuro
/// con varios workers). Por eso la proteccion real vive aqui, a nivel
/// de datos: si ya existe una Reading muy reciente para una planta, se
/// omite el guardado para esa planta en esta corrida.
"""
import logging
import os
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app import models
from app.database import SessionLocal
from app.plants.sensor_link import resolve_sensor

logger = logging.getLogger(__name__)

MIN_GUARD_SECONDS = 10.0


def _min_seconds_between_auto_readings() -> float:
    """
    Ventana anti-duplicados: la mitad del intervalo configurado (nunca
    menor a MIN_GUARD_SECONDS). No hace falta que coincida exactamente
    con la validacion de scheduler._interval_minutes(); ante un valor
    invalido simplemente se usa el default de 15 minutos.
    """
    raw = os.environ.get("AUTO_SAVE_INTERVAL_MINUTES", "15")
    try:
        interval_minutes = int(raw)
        if interval_minutes <= 0:
            interval_minutes = 15
    except ValueError:
        interval_minutes = 15
    return max(MIN_GUARD_SECONDS, (interval_minutes * 60) / 2)


def _seconds_since_last_reading(session: Session, plant_id: int) -> float | None:
    last = (
        session.query(models.Reading)
        .filter(models.Reading.plant_id == plant_id)
        .order_by(models.Reading.timestamp.desc())
        .first()
    )
    if last is None or last.timestamp is None:
        return None
    last_timestamp = last.timestamp
    if last_timestamp.tzinfo is None:
        last_timestamp = last_timestamp.replace(tzinfo=timezone.utc)
    return (datetime.now(timezone.utc) - last_timestamp).total_seconds()


def save_readings_for_all_plants(db: Session | None = None) -> None:
    """
    Si db es None, abre y cierra su propia sesion (uso real desde el
    scheduler). Si se pasa una sesion (tests), el caller es responsable
    de cerrarla; esta funcion no la cierra.
    """
    owns_session = db is None
    session = db if db is not None else SessionLocal()
    try:
        try:
            plants = session.query(models.Plant).all()
        except Exception:
            session.rollback()
            logger.exception(
                "Guardado automatico: no se pudo listar las plantas; "
                "se aborta esta corrida."
            )
            return

        guard_seconds = _min_seconds_between_auto_readings()
        for plant in plants:
            try:
                age_seconds = _seconds_since_last_reading(session, plant.id)
                if age_seconds is not None and age_seconds < guard_seconds:
                    logger.info(
                        "Guardado automatico omitido para planta id=%s: ya "
                        "hay una lectura de hace %.0fs (posible corrida "
                        "duplicada de otro proceso/scheduler).",
                        plant.id,
                        age_seconds,
                    )
                    continue

                sensor = resolve_sensor(plant, session)
                data = sensor.read()
                session.add(
                    models.Reading(
                        plant_id=plant.id,
                        temperature_c=data.temperature_c,
                        humidity_pct=data.humidity_pct,
                        pressure_hpa=data.pressure_hpa,
                    )
                )
                session.commit()
            except Exception:
                session.rollback()
                logger.exception(
                    "Guardado automatico fallo para planta id=%s (%s); "
                    "se continua con las demas.",
                    plant.id,
                    plant.name,
                )
    finally:
        if owns_session:
            session.close()
