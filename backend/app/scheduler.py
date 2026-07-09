"""
scheduler.py

/// <summary>
/// Arranca/detiene el job de guardado automatico via APScheduler
/// (BackgroundScheduler: thread de fondo, porque el resto de la app es
/// sincrona -- routers `def`, SQLAlchemy sync, y el driver real hace
/// subprocess.run bloqueante). Variables de entorno:
///   - AUTO_SAVE_ENABLED (default "true")
///   - AUTO_SAVE_INTERVAL_MINUTES (default "15")
/// </summary>
"""
import logging
import os

from apscheduler.schedulers.background import BackgroundScheduler

from app.jobs.auto_save import save_readings_for_all_plants

logger = logging.getLogger(__name__)

JOB_ID = "auto_save_readings"
_scheduler: BackgroundScheduler | None = None


def _is_enabled() -> bool:
    return os.environ.get("AUTO_SAVE_ENABLED", "true").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )


def _interval_minutes() -> int:
    raw = os.environ.get("AUTO_SAVE_INTERVAL_MINUTES", "15")
    try:
        value = int(raw)
        if value <= 0:
            raise ValueError
        return value
    except ValueError:
        logger.warning("AUTO_SAVE_INTERVAL_MINUTES=%r invalido; usando 15.", raw)
        return 15


def start_scheduler() -> None:
    global _scheduler
    if not _is_enabled():
        logger.info("Guardado automatico deshabilitado (AUTO_SAVE_ENABLED=false).")
        return
    if _scheduler is not None and _scheduler.running:
        return

    interval = _interval_minutes()
    _scheduler = BackgroundScheduler()
    _scheduler.add_job(
        save_readings_for_all_plants,
        "interval",
        minutes=interval,
        id=JOB_ID,
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=60,
    )
    _scheduler.start()
    logger.info("Guardado automatico iniciado: cada %s minuto(s).", interval)


def stop_scheduler() -> None:
    global _scheduler
    if _scheduler is None:
        return
    _scheduler.shutdown(wait=False)
    _scheduler = None
