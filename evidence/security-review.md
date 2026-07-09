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

## Segunda revision: scheduler de guardado automatico

Componente elegido: `backend/app/scheduler.py` + `backend/app/jobs/auto_save.py`
(el guardado periodico de lecturas, ver el feature agregado despues de
la primera revision). Se revisaron dos preguntas concretas: ¿puede
duplicarse el guardado si `uvicorn --reload` reinicia el proceso?, y
¿que pasa si un sensor falla durante un guardado automatico, afecta a
las demas plantas?

### 1. [CORREGIDO] Sin proteccion contra duplicados entre procesos

**Antes:** `start_scheduler()` ya evitaba duplicar el job **dentro de
un mismo proceso** (singleton `_scheduler` + `replace_existing=True`).
Pero esa proteccion vive en memoria de un solo proceso: no existe
ningun mecanismo que impida que **dos procesos distintos** terminen con
un `BackgroundScheduler` corriendo al mismo tiempo, cada uno guardando
lecturas para las mismas plantas. Escenarios reales donde esto puede
pasar:

- `uvicorn --reload`: al detectar un cambio de archivo, el reloader
  termina el proceso viejo y arranca uno nuevo. El apagado limpio
  (`stop_scheduler()` -> `scheduler.shutdown(wait=False)`) depende de
  que el proceso viejo reciba y procese la senal de apagado del ASGI
  lifespan antes de que el reloader lo mate. Si el proceso viejo tarda
  en reaccionar (o el reloader lo fuerza a terminar antes de que el
  lifespan de shutdown corra), puede haber una ventana breve con el
  scheduler viejo y el nuevo corriendo a la vez.
- Un despliegue futuro con varios workers (`--workers N`, o gunicorn
  con multiples procesos) haria que CADA worker arranque su propio
  scheduler de forma totalmente independiente — sin ningun cambio, esto
  multiplicaria por N cada lectura automatica guardada.

En ambos casos, el riesgo real no es un crash: es **duplicar filas** en
`readings` (y, en el caso de un sensor real, hacer lecturas fisicas
redundantes sin necesidad).

**Correccion aplicada:** en vez de intentar coordinar procesos (locks
distribuidos, etc. — desproporcionado para el alcance de este
proyecto), se agrego una salvaguarda **a nivel de datos**, independiente
de cuantos procesos esten corriendo: `save_readings_for_all_plants`
(`app/jobs/auto_save.py`) ahora consulta, antes de leer el sensor de
cada planta, si ya existe una `Reading` de esa planta mas reciente que
`_min_seconds_between_auto_readings()` (la mitad de
`AUTO_SAVE_INTERVAL_MINUTES`, con un piso de 10s) — y si es asi, omite
el guardado para esa planta en esa corrida (queda logueado, no es un
error silencioso). Como esta logica vive dentro del job automatico
(no en `POST /readings`), el boton manual "Guardar lectura actual"
sigue pudiendo forzar una lectura en cualquier momento, sin verse
afectado por esta ventana de proteccion.

Cubierto por los tests `test_skips_duplicate_run_within_guard_window` y
`test_does_not_skip_when_last_reading_is_older_than_guard_window` en
`tests/test_auto_save.py` (ciclo TDD: se escribieron antes de agregar
la salvaguarda, fallaron por la razon correcta — 2 lecturas en vez de
1 — y pasaron despues de implementarla).

### 2. [OK, con endurecimiento adicional] Fallo de sensor aislado por planta

**Revisado:** `save_readings_for_all_plants` ya envolvia la lectura de
cada planta (`resolve_sensor` + `sensor.read()` + `commit`) en su propio
`try/except Exception`, con `rollback()` + `logger.exception(...)` +
`continue`. Se confirmo que esto es correcto: como cada planta hace su
propio `commit()`, un fallo en la planta N no revierte lecturas ya
confirmadas de las plantas 1..N-1, y el loop sigue con la planta N+1.
Cubierto por `test_continues_when_one_plant_sensor_fails` (ya existia).

**Hallazgo menor corregido:** la consulta inicial
`session.query(models.Plant).all()` (para obtener la lista de plantas)
NO estaba protegida — si esa consulta fallaba (por ejemplo
`database is locked` por otro proceso escribiendo al mismo tiempo, un
escenario mas probable ahora que se identifico el punto 1), la
excepcion se propagaba fuera de la funcion. APScheduler la captura
internamente y no tumba el proceso, pero la corrida completa se perdia
sin dejar rastro en los logs propios de la app. Se envolvio esa
consulta en su propio `try/except` con `logger.exception(...)` antes de
seguir. Cubierto por `test_listing_plants_failure_is_contained_and_logged`.

### Resumen de la segunda revision

De 2 preguntas planteadas: la primera (duplicados entre procesos) si
era un riesgo real y se corrigio con una salvaguarda a nivel de datos
(no de proceso), con tests que la cubren; la segunda (aislamiento de
fallos de sensor) ya estaba bien implementada desde el primer ciclo
TDD del scheduler, y se le agrego un endurecimiento menor (proteger
tambien la consulta inicial de plantas) por la misma razon que motivo
el hallazgo 1.
