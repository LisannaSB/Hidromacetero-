/**
 * Gauge circular (elemento distintivo/"signature" del diseno): un anillo
 * de progreso que ubica la humedad actual dentro del rango ideal de la
 * planta, con zonas de color para "bajo / optimo / alto".
 */
export default function MoistureGauge({
  value = 0,
  min = 0,
  max = 100,
  idealMin,
  idealMax,
  size = 200,
  label = "Humedad ambiente",
}) {
  const radius = size / 2 - 14;
  const circumference = 2 * Math.PI * radius;
  const clamped = Math.min(Math.max(value, min), max);
  const pct = (clamped - min) / (max - min);
  const dash = circumference * pct;

  const idealStartPct = idealMin != null ? (idealMin - min) / (max - min) : null;
  const idealEndPct = idealMax != null ? (idealMax - min) / (max - min) : null;

  let ringColor = "var(--water-500)";
  if (idealMin != null && idealMax != null) {
    if (value < idealMin) ringColor = "var(--ochre-500)";
    else if (value > idealMax) ringColor = "var(--water-300)";
    else ringColor = "var(--leaf-500)";
  }

  return (
    <div className="moisture-gauge" style={{ width: size }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--soil-700)"
          strokeWidth="12"
        />
        {idealStartPct != null && idealEndPct != null && (
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke="var(--leaf-500)"
            strokeOpacity="0.25"
            strokeWidth="12"
            strokeDasharray={`${circumference * (idealEndPct - idealStartPct)} ${circumference}`}
            strokeDashoffset={-circumference * idealStartPct}
            transform={`rotate(-90 ${size / 2} ${size / 2})`}
          />
        )}
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke={ringColor}
          strokeWidth="12"
          strokeLinecap="round"
          strokeDasharray={`${dash} ${circumference}`}
          transform={`rotate(-90 ${size / 2} ${size / 2})`}
          style={{ transition: "stroke-dasharray 0.8s ease, stroke 0.5s ease" }}
        />
        <text
          x="50%"
          y="46%"
          textAnchor="middle"
          fontFamily="var(--font-display)"
          fontSize={size * 0.19}
          fill="var(--paper-100)"
        >
          {Math.round(value)}%
        </text>
        <text
          x="50%"
          y="62%"
          textAnchor="middle"
          fontFamily="var(--font-body)"
          fontSize={size * 0.06}
          fill="var(--muted-500)"
        >
          {label}
        </text>
      </svg>
    </div>
  );
}
