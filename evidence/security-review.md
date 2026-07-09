# Evidencia: revision de seguridad

Tema 5 de la asignacion: "Security". Endpoint elegido:
**`POST /irrigation/water`** — es el mas critico del sistema porque
acciona un actuador (bomba de riego), simulado hoy pero pensado para
conectarse a hardware real (motor/bomba) en el futuro. Un error aqui no
solo corrompe datos: puede desperdiciar agua o, con hardware real,
provocar inundacion de la maceta o dano al motor por sobre-uso.

Esta revision se hizo sobre el codigo real de este repositorio
(`backend/app/routers/irrigation.py`), no es un ejercicio generico.

## Hallazgos

### 1. [CORREGIDO] `liters` sin limite superior

**Antes:** si el cliente enviaba `liters` explicito en el body, el unico
control era `gt=0` en el schema (`IrrigationRequest`). Nada impedia pedir
`liters: 999999`, que el `SimulatedPumpDriver` aceptaria sin problema
(solo calcula `duration = liters / flow_rate`). Con un driver real de
hardware, esto se traduce directamente en inundar la maceta o mantener
un motor activo por horas.

**Correccion aplicada:** se agrego una validacion en el router que
rechaza (`400 Bad Request`) cualquier `liters` mayor a la capacidad de
la maceta (`plant.pot_volume_liters`). Ver el diff en
`app/routers/irrigation.py` y el test
`test_water_plant_rejects_liters_above_pot_capacity` en
`tests/test_irrigation.py` (evidencia de que el fix esta cubierto por
test, no es solo un comentario).

### 2. [ACEPTADO / limitacion documentada] Sin autenticacion ni rate limiting

El endpoint no tiene autenticacion ni limite de frecuencia de llamadas.
Cualquier cliente con acceso de red a la API puede disparar riegos
repetidamente. Para el alcance de esta asignacion (demo local, sin
despliegue publico) se acepta el riesgo, pero se documenta aqui como
limitacion conocida: **antes de exponer esta API fuera de una red local
de confianza, se debe agregar autenticacion (API key minima) y un limite
de frecuencia por planta** (por ejemplo, no permitir mas de un riego
cada N minutos, ademas del limite logico de `pot_volume_liters`).

### 3. [OK] Validacion de existencia de recurso

`plant_id` inexistente devuelve `404` antes de tocar el driver o la base
de datos — correcto, evita accionar el driver para un recurso que no
existe.

### 4. [OK] Sin inyeccion SQL

Todas las queries usan el ORM de SQLAlchemy con filtros parametrizados
(`.filter(models.Plant.id == payload.plant_id)`), no hay SQL crudo
concatenado en ningun router.

### 5. [OK] Timeout en el driver real del sensor

`DracalPTHSensor` (driver real, `app/sensor/dracal_pth.py`) usa
`subprocess.run(..., timeout=3.0)`, evitando que una falla del hardware
o del binario `dracal-usb-get` cuelgue la API indefinidamente.

## Resumen

De 5 puntos revisados: 1 hallazgo real fue corregido con test que lo
cubre, 1 riesgo se documenta como limitacion aceptada para este alcance,
y 3 puntos ya estaban correctos.
