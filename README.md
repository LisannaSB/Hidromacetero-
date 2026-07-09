# HidroMacetero

Dashboard de monitoreo ambiental en tiempo real para un macetero,
construido como practica de **Claude Code** (Phoenix Calibration DR —
asignacion "Claude Code en Practica").

Usa un sensor **Dracal VCP-PTH450-CAL** (temperatura, humedad relativa,
presion atmosferica) para recomendar cuanto y cuando regar una planta
(ejemplo: papa / *Solanum tuberosum*), calcular litros segun la
capacidad de la maceta, y simular la activacion de una bomba de riego.

> Lectura recomendada antes de tocar el codigo: **[`docs/GUIA.md`](docs/GUIA.md)**
> explica cada pieza del proyecto, como conectar el sensor real, y como
> generar la evidencia de uso de Claude Code que pide la asignacion.

## Screenshots conceptuales

El dashboard muestra: una ilustracion de la planta que cambia de animo
segun la humedad, un anillo de progreso ("gauge") con el rango ideal
resaltado, una tarjeta de recomendacion de riego con boton para
activarlo (simulado), y un historico en grafica de linea.

## Requisitos

- Python 3.11+
- Node.js 18+
- (Opcional, solo para hardware real) [DracalView](https://www.dracal.com)
  instalado, para tener el binario `dracal-usb-get` en el PATH.

## Como correrlo

### 1. Backend (FastAPI)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # o el equivalente en Windows
pip install -r requirements.txt
cp .env.example .env      # SENSOR_MODE=mock por defecto
uvicorn app.main:app --reload
```

La API queda en `http://127.0.0.1:8000`. Documentacion interactiva
(Swagger) en `http://127.0.0.1:8000/docs`.

### 2. Frontend (React + Vite)

```bash
cd frontend
npm install
cp .env.example .env      # VITE_API_URL=http://127.0.0.1:8000
npm run dev
```

Dashboard en `http://127.0.0.1:5173`. La primera vez te pedira crear un
perfil de planta (nombre, capacidad de la maceta en litros, rangos
ideales de humedad/temperatura).

### 3. Correr los tests

```bash
cd backend
pytest -q
```

Los tests siempre corren en modo mock (`SENSOR_MODE=mock` forzado en
`tests/conftest.py`), sin necesidad del sensor fisico.

## Conectar el sensor Dracal real

1. Instala [DracalView](https://www.dracal.com) (incluye el binario de
   linea de comandos `dracal-usb-get`).
2. Conecta el VCP-PTH450-CAL por USB. Verifica que se detecta:
   ```bash
   dracal-usb-get -l
   ```
3. En `backend/.env`, configura:
   ```
   SENSOR_MODE=real
   DRACAL_SERIAL=E25876   # el serial de tu sensor
   ```
4. Reinicia el backend. `GET /health` deberia reportar `"sensor_mode":
   "real"`.

**Nota honesta:** el VCP-PTH450-CAL mide temperatura, humedad y presion
del **aire**, no humedad directa del sustrato/tierra. La recomendacion
de riego de este proyecto usa la humedad ambiente como senal indirecta
combinada con el tiempo desde el ultimo riego — es una simplificacion
razonable para el alcance de esta asignacion, no un reemplazo de un
sensor capacitivo de suelo.

## Endpoints principales (3 casos de uso obligatorios)

| Metodo | Path | Descripcion |
|---|---|---|
| GET | `/readings/current` | Lectura actual del sensor (+ recomendacion de riego si se pasa `plant_id`) |
| POST | `/readings` | Persiste una lectura con timestamp |
| GET | `/readings?from=&to=` | Historial filtrado por rango de tiempo |

Endpoints adicionales de soporte: `/plants` (CRUD de perfiles de planta),
`/sensors` (registro y verificación de sensores físicos), `/irrigation/water`
(activa el riego simulado), `/health`.

## Múltiples sensores (uno por planta)

Si tienes varias plantas, cada una puede tener su propio sensor Dracal
físico asignado, en vez de compartir uno solo:

1. En el frontend, ve a **⚙ Sensores** (en la barra lateral) y registra
   cada sensor con un nombre y su número de serie (`E25876`, por ejemplo).
2. Dale a **"Verificar conexión"** — esto intenta leer el sensor de verdad
   (o simula la lectura si lo registraste en modo `mock`).
3. Al crear una planta nueva, selecciónalo en el campo **"Sensor asignado"**.
4. Si una planta no tiene sensor asignado, usa el sensor por defecto
   (configurado por `SENSOR_MODE`/`DRACAL_SERIAL` en `.env`), igual que antes.

## Estructura

Ver `CLAUDE.md` para el mapa completo de carpetas y convenciones del
proyecto.

## Evidencia de uso de Claude Code

Ver [`EVIDENCE.md`](EVIDENCE.md) y la carpeta `evidence/`.

## Licencia / uso

Proyecto academico de practica. Sin licencia de codigo abierto formal.
