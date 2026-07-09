import { useEffect, useRef, useState } from "react";
import { api } from "./api";
import PlantIllustration from "./components/PlantIllustration.jsx";
import PlantSensorPanel from "./components/PlantSensorPanel.jsx";
import MoistureGauge from "./components/MoistureGauge.jsx";
import WateringCard from "./components/WateringCard.jsx";
import PlantSetupForm from "./components/PlantSetupForm.jsx";
import PlantSidebar from "./components/PlantSidebar.jsx";
import ReadingsChart from "./components/ReadingsChart.jsx";
import SensorsPage from "./components/SensorsPage.jsx";
import "./styles/App.css";

const POLL_MS = 8000;

// Intervalo de guardado automatico configurado en el backend
// (ver backend/.env.example, AUTO_SAVE_INTERVAL_MINUTES). No hay
// endpoint que exponga este valor todavia, asi que se documenta aqui
// en un solo lugar para facilitar el ajuste si eso cambia.
const AUTO_SAVE_INTERVAL_MINUTES = 15;

// Cada cuanto se recalcula el texto "hace X" en pantalla, para que no
// quede congelado durante varios minutos entre renders del componente.
const RELATIVE_TIME_REFRESH_MS = 30000;

/// <summary>
/// Formatea, en espanol, el tiempo transcurrido desde un timestamp ISO
/// hasta ahora, en un formato relativo simple (minutos u horas).
/// </summary>
function formatRelativeTime(timestamp) {
  if (!timestamp) return "sin lecturas guardadas todavia";
  const then = new Date(timestamp);
  if (Number.isNaN(then.getTime())) return "sin lecturas guardadas todavia";

  const diffMs = Date.now() - then.getTime();
  const diffMin = Math.floor(diffMs / 60000);

  if (diffMin <= 0) return "hace menos de 1 min";
  if (diffMin < 60) return `hace ${diffMin} min`;

  const diffHours = Math.floor(diffMin / 60);
  if (diffHours === 1) return "hace 1 hora";
  return `hace ${diffHours} horas`;
}

export default function App() {
  const [view, setView] = useState("dashboard"); // "dashboard" | "sensors"
  const [plants, setPlants] = useState([]);
  const [plant, setPlant] = useState(null);
  const [addingNew, setAddingNew] = useState(false);
  const [current, setCurrent] = useState(null);
  const [readings, setReadings] = useState([]);
  const [watering, setWatering] = useState(false);
  const [loadingPlant, setLoadingPlant] = useState(true);
  const [error, setError] = useState(null);
  const [, setRelativeTimeTick] = useState(0);
  const pollRef = useRef(null);

  useEffect(() => {
    bootstrap();
    return () => clearInterval(pollRef.current);
  }, []);

  // Fuerza un re-render periodico solo para refrescar el texto
  // "hace X" del indicador de guardado automatico; no dispara ningun
  // fetch adicional.
  useEffect(() => {
    const relativeTimeInterval = setInterval(() => {
      setRelativeTimeTick((t) => t + 1);
    }, RELATIVE_TIME_REFRESH_MS);
    return () => clearInterval(relativeTimeInterval);
  }, []);

  async function bootstrap() {
    try {
      const list = await api.listPlants();
      setPlants(list);
      if (list.length > 0) {
        setPlant(list[0]);
      }
    } catch (e) {
      setError(
        "No se pudo conectar con la API. Verifica que el backend FastAPI " +
          "este corriendo en " + (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000")
      );
    } finally {
      setLoadingPlant(false);
    }
  }

  useEffect(() => {
    if (!plant) return;
    refreshCurrent();
    refreshHistory();
    pollRef.current = setInterval(refreshCurrent, POLL_MS);
    return () => clearInterval(pollRef.current);
  }, [plant]);

  async function refreshCurrent() {
    try {
      const data = await api.getCurrentReading(plant.id);
      setCurrent(data);
    } catch (e) {
      setError(e.message);
    }
  }

  async function refreshHistory() {
    try {
      const data = await api.listReadings({ plantId: plant.id });
      setReadings(data);
    } catch (e) {
      setError(e.message);
    }
  }

  function handleSelectPlant(plantId) {
    const selected = plants.find((p) => p.id === plantId);
    if (selected) {
      setPlant(selected);
      setCurrent(null);
      setReadings([]);
    }
  }

  async function handleCreatePlant(form) {
    const created = await api.createPlant(form);
    setPlants((prev) => [...prev, created]);
    setPlant(created);
    setAddingNew(false);
  }

  async function handleSaveReading() {
    await api.createReading({ plant_id: plant.id });
    await refreshHistory();
  }

  async function handleWater() {
    setWatering(true);
    try {
      await api.waterPlant(plant.id, current?.advice?.recommended_liters);
      const updated = await api.listPlants();
      setPlants(updated);
      setPlant(updated.find((p) => p.id === plant.id) || plant);
      await refreshCurrent();
    } finally {
      setWatering(false);
    }
  }

  const lastReading = readings.length > 0 ? readings[readings.length - 1] : null;
  const lastReadingRelativeTime = formatRelativeTime(lastReading?.timestamp);

  async function handleSensorReassigned() {
    const updated = await api.listPlants();
    setPlants(updated);
    const refreshedPlant = updated.find((p) => p.id === plant.id);
    if (refreshedPlant) setPlant(refreshedPlant);
    await refreshCurrent();
  }

  return (
    <div className="app-container">
      {!loadingPlant && plants.length > 0 && (
        <PlantSidebar
          plants={plants}
          currentPlantId={plant?.id}
          statusByPlantId={
            plant && current?.advice
              ? { [plant.id]: current.advice.humidity_status }
              : {}
          }
          onSelect={(id) => {
            handleSelectPlant(id);
            setView("dashboard");
          }}
          onAddNew={() => {
            setAddingNew(true);
            setView("dashboard");
          }}
          onGoToSensors={() => setView("sensors")}
        />
      )}

      <div className="app-shell">
        {view === "sensors" ? (
          <SensorsPage onBack={() => setView("dashboard")} />
        ) : (
          <>
            <header className="hero">
              <div className="hero__eyebrow">Phoenix Calibration DR &middot; Sensor Dracal VCP-PTH450-CAL</div>
              <h1>HidroMacetero</h1>
              <p className="hero__tagline">
                Monitoreo ambiental en tiempo real para tu macetero, con
                recomendaciones de riego a la medida de cada planta.
              </p>
              {current && (
                <div className="hero__readout">
                  <span>{current.temperature_c.toFixed(1)}&deg;C</span>
                  <span className="hero__sep">·</span>
                  <span>{current.humidity_pct.toFixed(1)}% HR</span>
                  <span className="hero__sep">·</span>
                  <span>{current.pressure_hpa.toFixed(1)} hPa</span>
                </div>
              )}
            </header>

            {error && <div className="banner-error">{error}</div>}

            {!loadingPlant && (plants.length === 0 || addingNew) && (
              <>
                <PlantSetupForm
                  onCreate={handleCreatePlant}
                  onGoToSensors={() => setView("sensors")}
                />
                {plants.length > 0 && (
                  <button
                    className="btn-secondary btn-cancel-add"
                    onClick={() => setAddingNew(false)}
                  >
                    Cancelar y volver a mis plantas
                  </button>
                )}
              </>
            )}

            {plant && current && !addingNew && (
              <main className="dashboard-grid">
                <section className="panel panel--illustration">
                  <PlantIllustration status={current.advice?.humidity_status || "optimo"} />
                  <p className="panel__caption">{plant.species}</p>
                </section>

                <section className="panel panel--gauge">
                  <MoistureGauge
                    value={current.humidity_pct}
                    idealMin={plant.ideal_humidity_min}
                    idealMax={plant.ideal_humidity_max}
                  />
                  <p className="panel__caption">
                    Rango ideal: {plant.ideal_humidity_min}% - {plant.ideal_humidity_max}%
                  </p>
                </section>

                <section className="panel panel--advice">
                  <WateringCard
                    advice={current.advice}
                    plant={plant}
                    onWater={handleWater}
                    watering={watering}
                  />
                </section>

                <section className="panel panel--chart">
                  <div className="panel__header">
                    <h3>Historial de lecturas</h3>
                    <button className="btn-secondary" onClick={handleSaveReading}>
                      Guardar lectura actual
                    </button>
                  </div>
                  <p className="panel__caption panel__caption--autosave">
                    <span className="autosave-dot" aria-hidden="true" />
                    Guardado automático cada {AUTO_SAVE_INTERVAL_MINUTES} min
                    {lastReading ? (
                      <> &middot; última lectura guardada {lastReadingRelativeTime}</>
                    ) : (
                      <> &middot; {lastReadingRelativeTime}</>
                    )}
                  </p>
                  <ReadingsChart readings={readings} />
                </section>

                <section className="panel panel--sensor">
                  <h3>Sensor de esta planta</h3>
                  <PlantSensorPanel
                    plant={plant}
                    onAssigned={handleSensorReassigned}
                    onGoToSensors={() => setView("sensors")}
                  />
                </section>
              </main>
            )}

            <footer className="app-footer">
              HidroMacetero v0.2 &middot; Proyecto Claude Code en Practica &middot;
              Backend FastAPI + SQLAlchemy + SQLite &middot; Sensores
              multiples asignables por planta
            </footer>
          </>
        )}
      </div>
    </div>
  );
}
