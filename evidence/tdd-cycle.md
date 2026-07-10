# Evidencia: ciclo TDD real

Tema 3 de la asignacion: "Test-driven Iteration". Esto documenta un
ciclo TDD completo (rojo -> implementacion -> verde) ejecutado realmente
durante la construccion de este proyecto, con la salida real de
`pytest` en cada paso (no recreada de memoria).

## Feature elegida

Endpoint nuevo: `GET /plants/{plant_id}/next-watering-estimate`, que
estima cuantas horas faltan para el proximo riego recomendado segun el
tiempo transcurrido desde el ultimo riego.

## Paso 1 — Rojo: escribir el test antes del endpoint

Archivo: `backend/tests/test_watering_estimate.py`

```python
def test_next_watering_estimate_returns_hours_remaining(client):
    plant_resp = client.post(
        "/plants",
        json={"name": "Papa TDD", "pot_volume_liters": 10},
    )
    plant_id = plant_resp.json()["id"]

    response = client.get(f"/plants/{plant_id}/next-watering-estimate")

    assert response.status_code == 200
    body = response.json()
    assert "hours_since_last_watering" in body
    assert "hours_until_recommended_watering" in body
    assert body["hours_until_recommended_watering"] == 0
```

Salida real de `pytest tests/test_watering_estimate.py -q` ANTES de
implementar el endpoint:

```
>       assert response.status_code == 200
E       assert 404 == 200
E        +  where 404 = <Response [404 Not Found]>.status_code

tests/test_watering_estimate.py:18: AssertionError
=========================== short test summary info ===========================
FAILED tests/test_watering_estimate.py::test_next_watering_estimate_returns_hours_remaining
1 failed, 1 warning in 0.05s
```

Confirma que el test falla por la razon correcta: el endpoint todavia no
existe (404), no un error de sintaxis ni de fixture.

## Paso 2 — Implementacion minima

1. Se agrego el schema `NextWateringEstimate` en `app/schemas.py`.
2. Se agrego el endpoint en `app/routers/plants.py`, reutilizando la
   constante `HOURS_WITHOUT_WATER_ALERT` ya existente en
   `app/plants/advisor.py` para no duplicar la regla de negocio.

## Paso 3 — Verde: correr toda la suite

Salida real de `pytest -q` DESPUES de implementar:

```
..............                                                           [100%]
=============================== warnings summary ===============================
...
14 passed, 2 warnings in 0.53s
```

Los 14 tests (los 13 previos + el nuevo) pasan sin romper nada existente.

## Segundo ciclo TDD: guardado automatico y periodico de lecturas

Feature: en vez de depender de que el usuario haga clic en "Guardar
lectura actual", el backend guarda sola una lectura por planta cada
`AUTO_SAVE_INTERVAL_MINUTES` (default 15), usando APScheduler
(`BackgroundScheduler`) arrancado/detenido con el `lifespan` de FastAPI,
y respetando el sensor asignado a cada planta via `resolve_sensor`.

### Paso 1 — Rojo: escribir los tests antes del modulo `scheduler.py`

Archivo: `backend/tests/test_scheduler.py` (17 tests: parseo de
`AUTO_SAVE_INTERVAL_MINUTES`/`AUTO_SAVE_ENABLED`, y arranque/apagado
del scheduler). Se escribio completo ANTES de que existiera
`app/scheduler.py`.

Salida real de `pytest tests/test_scheduler.py -q` ANTES de crear el
modulo:

```
=================================== ERRORS ====================================
__________________ ERROR collecting tests/test_scheduler.py ___________________
ImportError while importing test module '...\tests\test_scheduler.py'.
tests\test_scheduler.py:11: in <module>
    from app import scheduler
E   ImportError: cannot import name 'scheduler' from 'app' (...\app\__init__.py)
=========================== short test summary info ===========================
ERROR tests/test_scheduler.py
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
1 warning, 1 error in 0.87s
```

Confirma que falla por la razon correcta: el modulo `app/scheduler.py`
todavia no existe, no un error de sintaxis en el test.

### Paso 2 — Implementacion minima

1. Se agrego `apscheduler==3.10.4` a `requirements.txt` y se instalo.
2. Se creo `app/jobs/auto_save.py` con `save_readings_for_all_plants`,
   reutilizando `app.plants.sensor_link.resolve_sensor` (la misma
   funcion que ya usa `POST /readings`) para no duplicar la logica de
   resolucion de sensor por planta.
3. Se creo `app/scheduler.py` con `start_scheduler()`/`stop_scheduler()`
   sobre `BackgroundScheduler`, leyendo `AUTO_SAVE_ENABLED` y
   `AUTO_SAVE_INTERVAL_MINUTES` con `os.environ.get(...)` (misma
   convencion que `SENSOR_MODE`/`DRACAL_SERIAL`).
4. Se conecto en `app/main.py` via un `lifespan` de FastAPI
   (`start_scheduler()` antes del `yield`, `stop_scheduler()` despues).
5. Se agrego `AUTO_SAVE_ENABLED=false` en `tests/conftest.py` (junto a
   `SENSOR_MODE=mock`) para que ningun test dispare el scheduler real
   ni escriba en `hidromacetero.db`.

### Paso 3 — Verde: correr los tests nuevos y luego toda la suite

Salida real de `pytest tests/test_scheduler.py -q` DESPUES de
implementar:

```
.................                                                        [100%]
17 passed, 1 warning in 0.57s
```

Se agrego ademas `tests/test_auto_save.py` (cubre: guarda una lectura
por cada planta registrada, respeta el sensor asignado via
`resolve_sensor`, y si el sensor de una planta falla las demas siguen
guardandose sin propagar la excepcion). Salida real de `pytest -q`
sobre TODA la suite:

```
.............................................                            [100%]
45 passed, 2 warnings in 1.65s
```

Los 45 tests (los 24 previos + 17 nuevos de `test_scheduler.py` + 4
nuevos de `test_auto_save.py`) pasan sin romper nada existente.

## Tercer ciclo: primera corrida del scheduler no debe ser inmediata

Problema reportado: `start_scheduler()` registraba el job de APScheduler
con `add_job(..., minutes=interval, ...)` sin pasar `next_run_time`
explicito. La preocupacion es que, sin ese parametro, la primera
ejecucion del job podria disparar de inmediato al arrancar (o en cada
reinicio de `uvicorn --reload` durante desarrollo), generando lecturas
casi-duplicadas para cada planta antes de esperar el intervalo completo.

El fix pedido —pasar `next_run_time` explicito,
calculado como `datetime.now() + timedelta(minutes=interval)` dentro de
`start_scheduler()`— es la solucion correcta independientemente de si
el bug se reproduce siempre: elimina cualquier ambiguedad/race
condition sobre cuando dispara la primera corrida, la hace determinista
y explicita en el codigo y en el log, y no depende de la resolucion del
reloj del sistema operativo.

### Paso 1 — Test que confirma el comportamiento esperado

Se agrego `test_start_scheduler_first_run_is_not_immediate` en
`backend/tests/test_scheduler.py`: arranca el scheduler con
`AUTO_SAVE_INTERVAL_MINUTES=1` y verifica que
`scheduler._scheduler.get_job(scheduler.JOB_ID).next_run_time` este al
menos 50 segundos en el futuro respecto a `datetime.now()`.

Este test queda como regresion permanente: valida que la primera
corrida respeta el intervalo configurado y protegeria contra una
regresion futura donde alguien cambie el trigger a un patron que
dispare de inmediato (por ejemplo, si el scheduler ya esta corriendo
cuando se llama `add_job`).

### Paso 2 — Fix aplicado

En `backend/app/scheduler.py`, dentro de `start_scheduler()`:

```python
interval = _interval_minutes()
first_run = datetime.now() + timedelta(minutes=interval)
_scheduler = BackgroundScheduler()
_scheduler.add_job(
    save_readings_for_all_plants,
    "interval",
    minutes=interval,
    id=JOB_ID,
    replace_existing=True,
    max_instances=1,
    coalesce=True,
    misfire_grace_time=60,
    next_run_time=first_run,
)
_scheduler.start()
logger.info(
    "Guardado automatico iniciado: cada %s minuto(s); primera corrida a las %s.",
    interval,
    first_run,
)
```

`first_run` se recalcula en cada llamada a `start_scheduler()`, asi que
cubre tambien los reinicios de `uvicorn --reload` (cada reinicio del
proceso vuelve a esperar el intervalo completo antes de la primera
corrida).

### Paso 3 — Verde: suite completa

Salida real de `pytest backend/tests/test_scheduler.py -q`:

```
..................                                                       [100%]
18 passed, 1 warning in 0.10s
```

Salida real de `pytest -q` (toda la suite, corrida desde `backend/`):

```
.................................................                        [100%]
49 passed, 2 warnings in 1.54s
```

### Verificacion en vivo (~70s de espera real)

Se escribio un script standalone (fuera del repo, en el scratchpad de
la sesion, **no comiteado**) que: aisla una base SQLite en memoria
propia (`StaticPool`, igual patron que `tests/conftest.py::db_session`)
sin tocar `backend/hidromacetero.db` ni el proceso real del usuario,
crea una planta de prueba, arranca `scheduler.start_scheduler()` con
`AUTO_SAVE_INTERVAL_MINUTES=1`, verifica el estado inmediatamente
despues, espera 65 segundos reales, y vuelve a verificar.

Salida real obtenida:

```
[2026-07-09 15:40:05.160935] Planta de prueba creada: id=1
[2026-07-09 15:40:05.160935] scheduler.start_scheduler() llamado (AUTO_SAVE_INTERVAL_MINUTES=1, AUTO_SAVE_ENABLED=true)
[2026-07-09 15:40:05.179935] Readings para la planta INMEDIATAMENTE despues de start_scheduler(): 0 (esperado: 0)
[2026-07-09 15:40:05.179935] job.next_run_time = 2026-07-09 15:41:05.160935-04:00 (faltan ~60.0s)
[2026-07-09 15:40:05.179935] Esperando 65s reales a que dispare el job...
[2026-07-09 15:41:10.182065] Readings para la planta DESPUES de esperar 65s: 1 (esperado: 1)
    Reading id=1 timestamp=2026-07-09 19:41:05.182396 temp=23.8 hum=55.37 pres=1013.19
[2026-07-09 15:41:10.182065] Diferencia total entre start_scheduler() y la lectura confirmada: 65.0s
[2026-07-09 15:41:10.182603] scheduler.stop_scheduler() llamado. Verificacion OK.
```

Cero lecturas antes del intervalo, exactamente una lectura nueva
generada por el job despues de esperar el intervalo completo (a los
~60s, dentro de la ventana de 65s de espera), confirmando que la
primera corrida respeta `AUTO_SAVE_INTERVAL_MINUTES` y no dispara de
inmediato.

## Como reproducir tu propio ciclo TDD con Claude Code

Para que tu entrega tenga tu propia evidencia generada en vivo con la
CLI de Claude Code (no solo la de este scaffold):

1. Abre este repo con `claude` en la carpeta `backend/`.
2. Pidele: *"Vamos a agregar el endpoint X. Primero escribe el test que
   deberia fallar."*
3. Corre `pytest -q` tu mismo y pega la salida (el fallo) en este
   archivo o en uno nuevo dentro de `evidence/`.
4. Pidele a Claude Code que implemente el endpoint.
5. Vuelve a correr `pytest -q`, confirma que pasa, y pega esa salida
   tambien.
