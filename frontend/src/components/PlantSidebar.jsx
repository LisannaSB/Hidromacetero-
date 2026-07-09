/**
 * Barra lateral con la lista de plantas/maceteros. Reemplaza al selector
 * desplegable: cada planta es un item clickeable, con un punto de color
 * que resume su estado de humedad mas reciente (si ya se cargo).
 */
export default function PlantSidebar({ plants, currentPlantId, statusByPlantId = {}, onSelect, onAddNew, onGoToSensors }) {
  return (
    <aside className="plant-sidebar">
      <div className="plant-sidebar__title">Mis maceteros</div>

      <nav className="plant-sidebar__list">
        {plants.map((p) => {
          const status = statusByPlantId[p.id];
          const isActive = p.id === currentPlantId;
          return (
            <button
              key={p.id}
              className={`plant-sidebar__item ${isActive ? "is-active" : ""}`}
              onClick={() => onSelect(p.id)}
            >
              <span className={`plant-sidebar__dot status-${status || "unknown"}`} />
              <span className="plant-sidebar__name">{p.name}</span>
            </button>
          );
        })}
      </nav>

      <button className="plant-sidebar__add" onClick={onAddNew}>
        + Nueva planta
      </button>
      <button className="plant-sidebar__sensors" onClick={onGoToSensors}>
        ⚙ Sensores
      </button>
    </aside>
  );
}
