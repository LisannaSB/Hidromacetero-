# Evidencia: Documentation Guidelines

Tema 4 de la asignacion. Generado como parte de este proyecto:

## README principal

Ver [`README.md`](../README.md) en la raiz: instrucciones de instalacion,
como correr backend/frontend/tests, como conectar el sensor real, y tabla
de los 3 endpoints obligatorios.

## Comentarios XML en clases del dominio

Se aplico el formato `/// <summary>...</summary>` (pedido explicitamente
por la asignacion) en las clases de dominio principales:

- `backend/app/models.py` — clases `Plant`, `Reading`, `IrrigationEvent`.
- `backend/app/sensor/base.py` — interfaz `SensorInterface`.
- `backend/app/sensor/dracal_pth.py` — clase `DracalPTHSensor` (driver
  real).
- `backend/app/plants/advisor.py` — modulo de recomendacion de riego
  (docstring de modulo con la misma convencion).
- `backend/app/irrigation/motor_driver.py` — clases `PumpDriverInterface`
  y `SimulatedPumpDriver`.

## Guia extendida

[`docs/GUIA.md`](../docs/GUIA.md) — documento de referencia completo del
proyecto: arquitectura, decisiones de diseno, como generar el resto de la
evidencia, y como conectar hardware real.
