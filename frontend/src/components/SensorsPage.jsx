import { useEffect, useState } from "react";
import { api } from "../api";

const EMPTY_FORM = { name: "", serial: "", mode: "mock" };

function statusLabel(sensor) {
  if (!sensor.last_verified_at) return "Nunca verificado";
  if (sensor.last_status === "ok") return "Conectado";
  return "Error de conexion";
}

function statusClass(sensor) {
  if (!sensor.last_verified_at) return "unknown";
  return sensor.last_status === "ok" ? "ok" : "error";
}

/**
 * Pantalla de administracion de sensores: registrar uno nuevo (nombre +
 * numero de serie + modo mock/real) y verificar que responde antes de
 * asignarlo a una planta.
 */
export default function SensorsPage({ onBack }) {
  const [sensors, setSensors] = useState([]);
  const [form, setForm] = useState(EMPTY_FORM);
  const [saving, setSaving] = useState(false);
  const [verifyingId, setVerifyingId] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    load();
  }, []);

  async function load() {
    try {
      const data = await api.listSensors();
      setSensors(data);
    } catch (e) {
      setError(e.message);
    }
  }

  async function handleCreate(e) {
    e.preventDefault();
    setSaving(true);
    setError(null);
    try {
      await api.createSensor(form);
      setForm(EMPTY_FORM);
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setSaving(false);
    }
  }

  async function handleVerify(sensorId) {
    setVerifyingId(sensorId);
    try {
      await api.verifySensor(sensorId);
      await load();
    } catch (e) {
      setError(e.message);
    } finally {
      setVerifyingId(null);
    }
  }

  async function handleDelete(sensorId) {
    try {
      await api.deleteSensor(sensorId);
      await load();
    } catch (e) {
      setError(e.message);
    }
  }

  return (
    <div className="sensors-page">
      <div className="sensors-page__header">
        <h2>Sensores</h2>
        <button className="btn-secondary" onClick={onBack}>
          &larr; Volver al dashboard
        </button>
      </div>

      <p className="sensors-page__intro">
        Registra aqui cada sensor Dracal fisico que tengas (uno por
        macetero) con su numero de serie. Verifica la conexion antes de
        asignarlo a una planta desde el formulario de "Nueva planta".
      </p>

      {error && <div className="banner-error">{error}</div>}

      <form className="sensor-form" onSubmit={handleCreate}>
        <label>
          Nombre
          <input
            value={form.name}
            onChange={(e) => setForm({ ...form, name: e.target.value })}
            placeholder="Dracal balcon"
            required
          />
        </label>
        <label>
          Numero de serie
          <input
            value={form.serial}
            onChange={(e) => setForm({ ...form, serial: e.target.value })}
            placeholder="E25876"
            required
          />
        </label>
        <label>
          Modo
          <select
            value={form.mode}
            onChange={(e) => setForm({ ...form, mode: e.target.value })}
          >
            <option value="mock">Mock (sin hardware)</option>
            <option value="real">Real (Dracal fisico)</option>
          </select>
        </label>
        <button className="btn-primary" type="submit" disabled={saving}>
          {saving ? "Registrando..." : "Registrar sensor"}
        </button>
      </form>

      <div className="sensor-list">
        {sensors.length === 0 && (
          <p className="sensors-page__empty">
            Todavia no has registrado ningun sensor.
          </p>
        )}
        {sensors.map((s) => (
          <div key={s.id} className="sensor-card">
            <div className="sensor-card__info">
              <div className="sensor-card__name">{s.name}</div>
              <div className="sensor-card__meta">
                Serial: <code>{s.serial}</code> &middot; Modo: {s.mode}
              </div>
              <div className={`sensor-card__status status-${statusClass(s)}`}>
                {statusLabel(s)}
                {s.last_status === "error" && s.last_error && (
                  <span className="sensor-card__error"> — {s.last_error}</span>
                )}
              </div>
            </div>
            <div className="sensor-card__actions">
              <button
                className="btn-secondary"
                onClick={() => handleVerify(s.id)}
                disabled={verifyingId === s.id}
              >
                {verifyingId === s.id ? "Verificando..." : "Verificar conexion"}
              </button>
              <button className="btn-danger" onClick={() => handleDelete(s.id)}>
                Eliminar
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
