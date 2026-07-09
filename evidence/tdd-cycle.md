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
