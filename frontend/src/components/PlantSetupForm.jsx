import { useEffect, useState } from "react";
import { api } from "../api";

const DEFAULTS = {
  name: "Papa criolla - macetero balcon",
  species: "Solanum tuberosum (papa)",
  pot_volume_liters: 10,
  ideal_humidity_min: 60,
  ideal_humidity_max: 80,
  ideal_temp_min: 15,
  ideal_temp_max: 24,
  watering_fraction: 0.12,
  sensor_id: null,
};

export default function PlantSetupForm({ onCreate, onGoToSensors }) {
  const [form, setForm] = useState(DEFAULTS);
  const [saving, setSaving] = useState(false);
  const [sensors, setSensors] = useState([]);

  useEffect(() => {
    api
      .listSensors()
      .then(setSensors)
      .catch(() => setSensors([]));
  }, []);

  const update = (field) => (e) => {
    const raw = e.target.value;
    const isNumeric = field !== "name" && field !== "species";
    setForm({ ...form, [field]: isNumeric ? Number(raw) : raw });
  };

  const updateSensor = (e) => {
    const raw = e.target.value;
    setForm({ ...form, sensor_id: raw === "" ? null : Number(raw) });
  };

  const submit = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await onCreate(form);
    } finally {
      setSaving(false);
    }
  };

  return (
    <form className="plant-setup" onSubmit={submit}>
      <h2>Configura tu macetero</h2>
      <p className="plant-setup__intro">
        Estos datos definen cuanta agua recomendar y cuando avisarte que
        riegues, segun la especie y el tamano de la maceta.
      </p>

      <label>
        Nombre de la planta / maceta
        <input value={form.name} onChange={update("name")} required />
      </label>

      <label>
        Especie
        <input value={form.species} onChange={update("species")} />
      </label>

      <label>
        Sensor asignado
        <select value={form.sensor_id ?? ""} onChange={updateSensor}>
          <option value="">Sin sensor especifico (usar el sensor por defecto)</option>
          {sensors.map((s) => (
            <option key={s.id} value={s.id}>
              {s.name} ({s.serial}
              {s.last_status ? `, ${s.last_status === "ok" ? "conectado" : "con error"}` : ""})
            </option>
          ))}
        </select>
      </label>
      {onGoToSensors && (
        <button
          type="button"
          className="link-button"
          onClick={onGoToSensors}
        >
          + Registrar un sensor nuevo
        </button>
      )}

      <div className="plant-setup__grid">
        <label>
          Capacidad de la maceta (L)
          <input
            type="number"
            step="0.5"
            min="0.5"
            value={form.pot_volume_liters}
            onChange={update("pot_volume_liters")}
            required
          />
        </label>
        <label>
          Fraccion a regar por ciclo
          <input
            type="number"
            step="0.01"
            min="0.01"
            max="0.9"
            value={form.watering_fraction}
            onChange={update("watering_fraction")}
          />
        </label>
        <label>
          Humedad ideal min (%)
          <input
            type="number"
            value={form.ideal_humidity_min}
            onChange={update("ideal_humidity_min")}
          />
        </label>
        <label>
          Humedad ideal max (%)
          <input
            type="number"
            value={form.ideal_humidity_max}
            onChange={update("ideal_humidity_max")}
          />
        </label>
        <label>
          Temp. ideal min (C)
          <input
            type="number"
            value={form.ideal_temp_min}
            onChange={update("ideal_temp_min")}
          />
        </label>
        <label>
          Temp. ideal max (C)
          <input
            type="number"
            value={form.ideal_temp_max}
            onChange={update("ideal_temp_max")}
          />
        </label>
      </div>

      <button className="btn-primary" type="submit" disabled={saving}>
        {saving ? "Creando…" : "Crear macetero"}
      </button>
    </form>
  );
}
