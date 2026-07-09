import "./PlantIllustration.css";

/**
 * Ilustracion original (SVG dibujado a mano en codigo) de una maceta con
 * una planta de papa. El estado animo (hojas erguidas vs. caidas, color)
 * responde al estado de humedad para dar feedback visual inmediato.
 */
export default function PlantIllustration({ status = "optimo", size = 220 }) {
  const wilted = status === "bajo";
  const soaked = status === "alto";

  const leafColor = wilted ? "var(--ochre-300)" : "var(--leaf-400)";
  const leafColorDark = wilted ? "var(--ochre-500)" : "var(--leaf-500)";
  const potColor = "var(--clay-500)";

  return (
    <svg
      className={`plant-illustration ${wilted ? "is-wilted" : ""} ${soaked ? "is-soaked" : ""}`}
      viewBox="0 0 220 220"
      width={size}
      height={size}
      role="img"
      aria-label={`Ilustracion de planta de papa, estado de humedad ${status}`}
    >
      <ellipse cx="110" cy="196" rx="70" ry="9" fill="#000" opacity="0.25" />

      {/* Maceta */}
      <path
        d="M62 140 L74 205 Q110 214 146 205 L158 140 Z"
        fill={potColor}
      />
      <path d="M62 140 L158 140 L152 152 L68 152 Z" fill="#a4573d" />
      <ellipse cx="110" cy="140" rx="48" ry="9" fill="#8a4936" />

      {/* Tierra */}
      <ellipse cx="110" cy="138" rx="40" ry="6.5" fill="#3a2a1c" />

      {/* Tallo */}
      <g className="plant-stem">
        <path
          d="M110 138 C 106 112, 108 90, 110 70"
          stroke={leafColorDark}
          strokeWidth="5"
          fill="none"
          strokeLinecap="round"
        />
        <path
          d="M110 118 C 122 108, 132 100, 128 84"
          stroke={leafColorDark}
          strokeWidth="4"
          fill="none"
          strokeLinecap="round"
        />
        <path
          d="M108 100 C 96 92, 86 86, 88 70"
          stroke={leafColorDark}
          strokeWidth="4"
          fill="none"
          strokeLinecap="round"
        />
      </g>

      {/* Hojas (grupo animado que se inclina si esta marchita) */}
      <g className="plant-leaves" style={{ transformOrigin: "110px 138px" }}>
        <ellipse cx="128" cy="80" rx="20" ry="12" fill={leafColor} transform="rotate(-25 128 80)" />
        <ellipse cx="88" cy="66" rx="22" ry="13" fill={leafColor} transform="rotate(20 88 66)" />
        <ellipse cx="110" cy="58" rx="18" ry="24" fill={leafColor} />
        <ellipse cx="112" cy="96" rx="16" ry="10" fill={leafColorDark} transform="rotate(-10 112 96)" />

        {soaked && (
          <>
            <circle cx="96" cy="70" r="2.6" fill="var(--water-300)" opacity="0.9" />
            <circle cx="120" cy="60" r="2.2" fill="var(--water-300)" opacity="0.8" />
            <circle cx="106" cy="86" r="2" fill="var(--water-300)" opacity="0.8" />
          </>
        )}
      </g>
    </svg>
  );
}
