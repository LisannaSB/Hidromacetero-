"""
main.py

/// <summary>
/// Punto de entrada de la API HidroMacetero. Registra los routers de
/// readings (casos de uso obligatorios), plants, irrigation y sensors,
/// configura CORS para el frontend de React y crea las tablas SQLite al
/// arrancar.
/// </summary>
"""
from dotenv import load_dotenv

# CRITICO: cargar .env ANTES de importar cualquier modulo que lea
# variables de entorno a nivel de modulo (por ejemplo
# app.sensor.dracal_pth, que lee DRACAL_BINARY al importarse). Si esto se
# hiciera despues, SENSOR_MODE/DRACAL_SERIAL/DRACAL_BINARY del .env
# nunca surtirian efecto.
load_dotenv()

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.db_migrate import ensure_plant_sensor_column
from app.routers import irrigation, plants, readings, sensors
from app.scheduler import start_scheduler, stop_scheduler

Base.metadata.create_all(bind=engine)
ensure_plant_sensor_column(engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(
    title="HidroMacetero API",
    description=(
        "Dashboard de monitoreo ambiental en tiempo real para macetas, "
        "usando el sensor Dracal VCP-PTH450-CAL (temperatura, humedad, "
        "presion) para recomendar riego segun el perfil de la planta."
    ),
    version="0.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(readings.router)
app.include_router(plants.router)
app.include_router(irrigation.router)
app.include_router(sensors.router)


@app.get("/health", tags=["health"])
def health_check():
    from app.sensor import get_sensor

    sensor = get_sensor()
    return {"status": "ok", "sensor_mode": "mock" if sensor.is_mock else "real"}
