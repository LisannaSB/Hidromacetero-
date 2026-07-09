import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend,
} from "recharts";

function formatTime(ts) {
  const d = new Date(ts);
  return d.toLocaleTimeString("es-DO", { hour: "2-digit", minute: "2-digit" });
}

export default function ReadingsChart({ readings }) {
  const data = readings.map((r) => ({
    time: formatTime(r.timestamp),
    Humedad: r.humidity_pct,
    Temperatura: r.temperature_c,
  }));

  if (data.length === 0) {
    return (
      <div className="chart-empty">
        Aun no hay lecturas guardadas en el historial. Presiona "Guardar
        lectura" para empezar a registrar datos.
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={280}>
      <LineChart data={data} margin={{ top: 8, right: 16, left: -12, bottom: 0 }}>
        <CartesianGrid stroke="var(--soil-700)" strokeDasharray="4 6" />
        <XAxis dataKey="time" stroke="var(--muted-500)" fontSize={12} />
        <YAxis stroke="var(--muted-500)" fontSize={12} />
        <Tooltip
          contentStyle={{
            background: "var(--soil-900)",
            border: "1px solid var(--soil-700)",
            borderRadius: 10,
            color: "var(--paper-100)",
          }}
        />
        <Legend />
        <Line
          type="monotone"
          dataKey="Humedad"
          stroke="var(--water-500)"
          strokeWidth={2.5}
          dot={false}
        />
        <Line
          type="monotone"
          dataKey="Temperatura"
          stroke="var(--ochre-500)"
          strokeWidth={2.5}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
