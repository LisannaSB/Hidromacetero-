const BASE_URL = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

async function request(path, options = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    const detail = await res.text();
    throw new Error(`${res.status} ${res.statusText}: ${detail}`);
  }
  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  getCurrentReading: (plantId) =>
    request(`/readings/current${plantId ? `?plant_id=${plantId}` : ""}`),
  createReading: (payload) =>
    request("/readings", { method: "POST", body: JSON.stringify(payload || {}) }),
  listReadings: ({ from, to, plantId } = {}) => {
    const params = new URLSearchParams();
    if (from) params.set("from", from);
    if (to) params.set("to", to);
    if (plantId) params.set("plant_id", plantId);
    const qs = params.toString();
    return request(`/readings${qs ? `?${qs}` : ""}`);
  },
  listPlants: () => request("/plants"),
  createPlant: (payload) =>
    request("/plants", { method: "POST", body: JSON.stringify(payload) }),
  waterPlant: (plantId, liters) =>
    request("/irrigation/water", {
      method: "POST",
      body: JSON.stringify({ plant_id: plantId, liters, triggered_by: "manual" }),
    }),
  irrigationHistory: (plantId) => request(`/irrigation/history/${plantId}`),

  listSensors: () => request("/sensors"),
  createSensor: (payload) =>
    request("/sensors", { method: "POST", body: JSON.stringify(payload) }),
  verifySensor: (sensorId) =>
    request(`/sensors/${sensorId}/verify`, { method: "POST" }),
  deleteSensor: (sensorId) =>
    request(`/sensors/${sensorId}`, { method: "DELETE" }),
  assignSensor: (plantId, sensorId) =>
    request(`/plants/${plantId}/sensor`, {
      method: "PATCH",
      body: JSON.stringify({ sensor_id: sensorId }),
    }),
};

export { BASE_URL };
