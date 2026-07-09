import { useState } from "react";

export default function WateringCard({ advice, plant, onWater, watering }) {
  const [justWatered, setJustWatered] = useState(false);

  if (!advice) return null;

  const handleWater = async () => {
    await onWater();
    setJustWatered(true);
    setTimeout(() => setJustWatered(false), 4000);
  };

  return (
    <div className={`watering-card ${advice.should_water ? "needs-water" : "is-fine"}`}>
      <div className="watering-card__header">
        <span className="watering-card__badge">
          {advice.should_water ? "Regar ahora" : "Todo en orden"}
        </span>
        <h3>{plant?.name}</h3>
      </div>
      <p className="watering-card__reason">{advice.reason}</p>

      {advice.should_water && (
        <div className="watering-card__action">
          <div className="watering-card__liters">
            <strong>{advice.recommended_liters} L</strong>
            <span>
              recomendados de {plant?.pot_volume_liters} L de capacidad de la
              maceta
            </span>
          </div>
          <button
            className="btn-primary"
            onClick={handleWater}
            disabled={watering || justWatered}
          >
            {justWatered
              ? "Riego simulado ✓"
              : watering
              ? "Regando…"
              : "Activar riego (simulado)"}
          </button>
        </div>
      )}
    </div>
  );
}
