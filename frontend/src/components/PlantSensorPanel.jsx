import { useEffect, useState } from "react";
import { api } from "../api";

/**
 * Muestra el sensor actualmente asignado a la planta activa y permite
 * cambiarlo (o quitarlo) sin tener que recrear la planta.
 */
export default function PlantSensorPanel({ plant, onAssigned, onGoToSensors }) {
  const [sensors, setSensors] = useState([]);
  const [selected, setSelected] = useState(plant.sensor_id ?? "");
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api
      .listSensors()
      .then(setSensors)
      .catch(() => setSensors([]));
  }, []);

  useEffect(() => {
    setSelected(plant.sensor_id ?? "");
  }, [plant.id, plant.sensor_id]);

  const currentSensor = sensors.find((s) => s.id === plant.sensor_id);

  async function handleSave() {
    setSaving(true);
    try {
      const sensorId = selected === "" ? null : Number(selected);
      await api.assignSensor(plant.id, sensorId);
      await onAssigned();
    } finally {
      setSaving(false);
    }
  }

  const changed = (selected === "" ? null : Number(selected)) !== (plant.sensor_id ?? null);

  return (
    <div className="sensor-panel">
      <div className="sensor-panel__current">
        Sensor actual:{" "}
        {currentSensor ? (
          <strong>
            {currentSensor.name} ({currentSensor.serial})
          </strong>
        ) : (
          <strong>Ninguno — usando el sensor por defecto</strong>
        )}
      </div>

      <div className="sensor-panel__controls">
        <select value={selected} onChange={(e) => setSelected(e.target.value)}>
          <option value="">Sin sensor especifico (usar el sensor por defecto)</option>
          {sensors.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name} ({s.serial}
              {s.last_status ? `, ${s.last_status === "ok" ? "conectado" : "con error"}` : ""})
            </option>
          ))}
        </select>
        <button className="btn-secondary" onClick={handleSave} disabled={!changed || saving}>
          {saving ? "Guardando..." : "Guardar"}
        </button>
      </div>

      <button type="button" className="link-button" onClick={onGoToSensors}>
        Administrar sensores
      </button>
    </div>
  );
}
