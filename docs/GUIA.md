# Guia completa de HidroMacetero

Este documento explica **todo** el proyecto: que se construyo, por que,
como correrlo, como conectar el hardware real, como estan organizados
los subagentes/skill/hook de Claude Code, y como completar la evidencia
que falta para la asignacion.

---

## 1. Que resuelve este proyecto

Un dashboard que:

1. Lee temperatura, humedad relativa y presion atmosferica de un sensor
   **Dracal VCP-PTH450-CAL** (o de un mock si no tienes el sensor a mano).
2. Compara esa lectura contra el perfil de una planta (ejemplo: papa /
   *Solanum tuberosum*) para decidir si hay que regar.
3. Calcula cuantos litros regar segun la capacidad de la maceta.
4. Simula la activacion de una bomba/motor de riego (driver simulado,
   listo para reemplazarse por hardware real).
5. Guarda un historial de lecturas y lo grafica en el tiempo.

Y, en paralelo, cumple los requisitos de la asignacion "Claude Code en
Practica": 3 casos de uso exactos, `CLAUDE.md`, evidencia de 8 temas de
Claude Code, un skill personalizado y un hook personalizado.

---

## 2. Por que la humedad "ambiente" y no "del sustrato"

Esto es importante y esta documentado en varios lugares del repo a
proposito (CLAUDE.md, README, advisor.py): el VCP-PTH450-CAL mide
temperatura/humedad/presion del **aire**, con sus tres canales reales
(`Pressure`, `Temperature`, `Relative Humidity`). No tiene una sonda que
se entierre en la tierra.

Para no presentar un dato enganoso, la logica de recomendacion
(`backend/app/plants/advisor.py`) combina:

- Humedad ambiente vs. rango ideal de la especie.
- Tiempo transcurrido desde el ultimo riego (si pasaron mas de 48h sin
  regar, se recomienda regar igual, sin importar la humedad del aire).
- Temperatura vs. rango ideal (temperaturas altas aumentan la
  evapotranspiracion, lo cual se menciona en la razon dada al usuario).

Si mas adelante quieres una medicion directa de humedad de sustrato, se
puede sumar un sensor capacitivo de suelo (ej. sensores tipo higrometro
capacitivo para Arduino/ESP32) implementando la misma interfaz
`SensorInterface` o una nueva `SoilMoistureInterface` — el diseño ya deja
espacio para eso sin tocar el resto del sistema.

---

## 3. Arquitectura del backend

```
Cliente (React) 
   │  HTTP/JSON
   ▼
FastAPI routers (readings, plants, irrigation)
   │
   ├── app/plants/advisor.py   -> logica de recomendacion (pura, testeable)
   ├── app/sensor/             -> SensorInterface (mock | Dracal real)
   ├── app/irrigation/         -> PumpDriverInterface (simulado | futuro real)
   └── app/models.py + database.py -> SQLAlchemy / SQLite
```

**Por que esta separacion:** los routers no deciden nada por si mismos
(no calculan litros, no deciden si regar) — solo orquestan. Eso permite
testear `advisor.py` con pruebas unitarias rapidas (`test_advisor.py`,
sin HTTP) y cambiar el sensor o el driver de riego sin tocar los
endpoints.

### Los 3 endpoints obligatorios

```
GET  /readings/current              -> lectura en vivo (+ advice si mandas plant_id)
POST /readings                      -> guarda una lectura (usa el sensor si no envias valores)
GET  /readings?from=&to=&plant_id=  -> historial filtrado
```

### Endpoints de soporte

```
POST /plants                                -> crear perfil de planta
GET  /plants                                -> listar plantas
GET  /plants/{id}                           -> ver una planta
GET  /plants/{id}/next-watering-estimate    -> horas estimadas para el proximo riego
POST /irrigation/water                      -> accionar riego (simulado)
GET  /irrigation/history/{plant_id}         -> historial de riegos
GET  /health                                -> estado de la API y modo del sensor
```

---

## 4. Arquitectura del frontend

`App.jsx` hace polling de `/readings/current` cada 8 segundos y muestra:

- **`PlantIllustration`**: SVG original (dibujado en codigo, sin assets
  externos) de una papa en maceta. Las hojas se "caen" visualmente si la
  humedad esta baja.
- **`MoistureGauge`**: anillo de progreso con la zona ideal resaltada —
  el elemento "firma" del diseno.
- **`WateringCard`**: explica en texto por que hay (o no) que regar, y
  tiene el boton para activar el riego simulado.
- **`ReadingsChart`**: grafica de linea (Recharts) con el historico de
  humedad y temperatura.
- **`PlantSetupForm`**: formulario inicial para crear el perfil de la
  planta/maceta (capacidad en litros, rangos ideales).

Paleta y tipografia estan centralizadas en `src/styles/theme.css` como
variables CSS — cambia los valores ahi, no hardcodees colores nuevos en
los componentes.

---

## 5. Los subagentes de Claude Code

En `.claude/agents/` hay 3 subagentes:

- **`design-agent`**: decisiones visuales (paleta, tipografia,
  ilustraciones SVG, accesibilidad).
- **`frontend-agent`**: componentes React, consumo de la API, estado del
  dashboard.
- **`backend-agent`**: endpoints FastAPI, modelos, sensor, TDD,
  revisiones de seguridad.

Claude Code los detecta automaticamente por su `description` y los
invoca cuando el pedido calza (por ejemplo, "cambia el color del boton
de riego" activaria a `design-agent`). Tambien puedes invocarlos
explicitamente: *"usa el subagente backend-agent para agregar un
endpoint de exportacion CSV"*.

---

## 6. El skill personalizado

`.claude/skills/fastapi-endpoint-generator/SKILL.md` estandariza como se
agrega un endpoint nuevo al backend: primero el test (rojo), luego el
schema, el modelo si aplica, el router, y por ultimo registrar el router
en `main.py`. Claude Code lo activa solo cuando detecta un pedido tipo
"agrega un endpoint para...".

---

## 7. El hook personalizado

`.claude/hooks/pre-commit-guard.sh` (registrado en `.claude/settings.json`
como `PreToolUse` sobre la herramienta `Bash`) intercepta cualquier
comando de bash que contenga `git commit` y bloquea el commit si:

- Hay un archivo `.env` real (no `.env.example`) en staging.
- El diff en staging contiene texto que parece una API key/token/password
  hardcodeada.

Ya se probo en vivo durante la construccion de este proyecto (ver
`evidence/security-review.md` y el propio script, que incluye el
contrato de entrada/salida esperado por Claude Code).

---

## 8. Conectar el hardware real

### Sensor Dracal VCP-PTH450-CAL

Ver la seccion correspondiente en `README.md`. En resumen:
`SENSOR_MODE=real` + `DRACAL_SERIAL=<tu serial>` en `backend/.env`, con
DracalView instalado (para tener `dracal-usb-get` en el PATH).

### Riego automatizado (motor/bomba)

Hoy `SimulatedPumpDriver` (`backend/app/irrigation/motor_driver.py`) solo
imprime logs y calcula tiempos — no mueve ningun motor real. Si en algun
momento consigues un driver tipo L298N (puente H) o un modulo de rele
para una micro-bomba de 12V:

1. Crea una clase `RealPumpDriver(PumpDriverInterface)` en el mismo
   archivo o en uno nuevo (`gpio_pump_driver.py`).
2. Implementa `dispense(liters)` activando el pin GPIO correspondiente
   por `liters / flow_rate_lps` segundos (usa `RPi.GPIO` o `gpiozero` si
   es una Raspberry Pi).
3. Cambia `get_pump_driver()` para elegir la implementacion real segun
   una variable de entorno, igual que se hizo con el sensor
   (`SENSOR_MODE`).

No se implemento el driver real en este scaffold porque no hay hardware
de riego fisico conectado — la simulacion es intencional y esta
documentada como tal en `CLAUDE.md`.

---

## 9. Subir el proyecto a GitHub

```bash
cd hidromacetero
git init
git add .
git commit -m "Proyecto inicial: HidroMacetero"
git branch -M main
git remote add origin https://github.com/<tu-usuario>/hidromacetero.git
git push -u origin main
```

Recuerda: el repositorio debe ser **privado** si contiene informacion que
no quieras publica (aunque este proyecto no incluye secretos, ya que
`.env` esta en `.gitignore`).

Despues de subirlo, completa la evidencia de GitHub MCP (tema 6) — ver
`evidence/github-mcp-usage.md` para el paso a paso.

---

## 10. Que falta que hagas tu (para que la evidencia sea 100% autentica)

Este scaffold te deja el proyecto funcional y la mayoria de la evidencia
ya generada y verificada (tests reales corridos, hook real probado,
revision de seguridad real con un fix real). Sin embargo, para que la
entrega refleje **tu propio uso de la CLI de Claude Code** (que es lo que
la asignacion evalua), te recomendamos:

1. Clonar/descomprimir este proyecto localmente.
2. Abrirlo con `claude` (la CLI real) en la raiz.
3. Pedirle una funcionalidad pequena nueva usando Plan Mode explicitamente.
4. Completar la evidencia de GitHub MCP (tema 6) con una accion real en
   tu cuenta.
5. Revisar y, si quieres, personalizar el skill/hook con tu propio toque.

Con eso tendrias evidencia genuina generada por ti con la herramienta que
la asignacion pide evaluar, sobre una base solida ya construida y
probada.
