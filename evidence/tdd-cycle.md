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
