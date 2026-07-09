# CLAUDE.md

Contexto de proyecto para Claude Code. Lee esto antes de planear o
implementar cualquier cambio.

## Que es este proyecto

**HidroMacetero**: dashboard de monitoreo ambiental en tiempo real para un
macetero (planta de papa como caso de ejemplo), usando el sensor Dracal
VCP-PTH450-CAL (temperatura, humedad relativa, presion atmosferica).
El backend interpreta la lectura + el perfil de la planta para recomendar
cuanto y cuando regar, y puede accionar (de forma simulada) una bomba de
riego.

Este repositorio es, ademas, la entrega de la asignacion "Claude Code en
Practica" de Phoenix Calibration DR (ver `docs/asignacion_original.docx`
o el PDF equivalente si fue convertido). Cualquier decision de alcance
debe priorizar cumplir los 3 casos de uso obligatorios y los 8 temas de
Claude Code exigidos por esa asignacion antes que anadir features nuevas.

## Stack

- **Backend**: FastAPI + SQLAlchemy 2.x + SQLite + pytest. Python 3.11+.
- **Frontend**: React 18 + Vite. Sin TypeScript (mantener JS simple).
- Gráficas: Recharts.
- **Hardware**: sensor Dracal VCP-PTH450-CAL (serial de referencia:
  `E25876`), accedido via el binario oficial `dracal-usb-get`. Abstraido
  detras de `SensorInterface` con dos implementaciones: `MockDracalSensor`
  (por defecto) y `DracalPTHSensor` (real).
- Riego: `PumpDriverInterface` con `SimulatedPumpDriver` (no hay hardware
  de riego fisico conectado; queda simulado a proposito).

## Estructura de carpetas

```
backend/app/
  main.py              # entrypoint FastAPI, registra routers
  database.py          # engine/session SQLAlchemy (SQLite)
  models.py            # Plant, Reading, IrrigationEvent
  schemas.py           # Pydantic request/response
  sensor/              # interfaz + mock + driver real Dracal
  plants/advisor.py    # logica de recomendacion de riego
  irrigation/motor_driver.py  # driver simulado de bomba/motor
  routers/             # readings.py (3 casos de uso), plants.py, irrigation.py
backend/tests/         # pytest, SENSOR_MODE=mock forzado en conftest.py
frontend/src/
  App.jsx              # layout y estado principal
  api.js               # cliente fetch hacia el backend
  components/          # MoistureGauge, PlantIllustration, WateringCard, etc.
  styles/              # theme.css (tokens), App.css (layout)
.claude/
  agents/              # subagentes: design, frontend, backend
  skills/              # skill personalizado (fastapi-endpoint-generator)
  hooks/               # hook personalizado + settings.json
evidence/              # evidencia de uso de Claude Code (ver EVIDENCE.md)
docs/                  # GUIA.md y material de referencia
```

## Convenciones

- **Idioma**: docstrings, comentarios y mensajes de commit en espanol.
  Nombres de variables/funciones en ingles (convencion de codigo).
- **Comentarios de clase estilo XML** (`/// <summary>...</summary>`) en
  clases del dominio (modelos, drivers, logica de negocio), tal como
  pide el tema "Documentation Guidelines" de la asignacion.
- **SENSOR_MODE** controla el sensor: `mock` (default, para dev y tests)
  o `real` (requiere DracalView instalado y `DRACAL_SERIAL` configurado).
  Nunca asumir que el hardware real esta disponible; todo endpoint y test
  debe funcionar en modo mock.
- Los 3 endpoints de `routers/readings.py` son el nucleo evaluado de la
  asignacion: **no renombrar ni cambiar sus contratos** (`GET
  /readings/current`, `POST /readings`, `GET /readings?from=&to=`) sin
  actualizar tambien `EVIDENCE.md` y los tests.
- Toda funcionalidad no trivial nueva pasa primero por **Plan Mode**
  (ver tema 1 de la asignacion) antes de implementarse.
- Los tests de pytest deben poder correr sin hardware conectado
  (`SENSOR_MODE=mock` ya esta forzado en `tests/conftest.py`).

## Restricciones

- No usar Alembic ni migraciones: la base es SQLite de desarrollo, creada
  con `Base.metadata.create_all` al arrancar. Fuera de alcance para esta
  asignacion.
- No agregar autenticacion/usuarios: fuera del alcance de los 3 casos de
  uso pedidos.
- No commitear `*.db`, `node_modules/`, ni `.env` (ver `.gitignore`).
- El driver de riego (`SimulatedPumpDriver`) debe permanecer simulado por
  defecto: no hay hardware de motor conectado. Si en el futuro se integra
  un driver real (p. ej. L298N via GPIO), debe implementar la misma
  interfaz `PumpDriverInterface` sin romper `routers/irrigation.py`.
- El Dracal PTH450 mide humedad del **aire**, no humedad de sustrato. No
  presentar los datos como si fueran una medicion directa de humedad de
  tierra en la UI ni en la documentacion: usar siempre "humedad ambiente".

## Comandos utiles

```bash
# Backend
cd backend
pip install -r requirements.txt --break-system-packages
uvicorn app.main:app --reload          # http://127.0.0.1:8000
pytest -q                               # correr toda la suite

# Frontend
cd frontend
npm install
npm run dev                             # http://127.0.0.1:5173
```

## Que se evalua en este repositorio (resumen)

Ver `asignacion original` para el detalle completo. En resumen: 30%
funcionalidad de los 3 endpoints + tests, 40% evidencia de uso de los 8
temas de Claude Code (`EVIDENCE.md`), 20% arquitectura/calidad, 10% skill
+ hook creados.
