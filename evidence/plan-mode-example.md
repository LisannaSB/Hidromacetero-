# Evidencia: Plan Mode + Ask Mode

Tema 1 de la asignacion. Este documento recoge el plan real que se siguio
para construir HidroMacetero, tal como se habria producido en **Plan
Mode** de Claude Code antes de tocar codigo (aqui reconstruido en el
formato en que Plan Mode lo habria presentado).

## Pregunta inicial (Ask Mode)

> "Tengo un sensor Dracal VCP-PTH450-CAL. Quiero usarlo para saber
> cuanta humedad necesita una planta de papa en una maceta, avisarme
> cuando regar, calcular litros segun la capacidad de la maceta, y
> simular un driver de motor de riego. Debe cumplir exactamente los 3
> casos de uso de la asignacion (lectura actual, guardar lectura,
> historial por rango)."

## Plan propuesto

1. **Modelo de datos**: `Plant` (perfil: capacidad en litros, rangos
   ideales de humedad/temperatura, ultima fecha de riego), `Reading`
   (lecturas del sensor con timestamp), `IrrigationEvent` (historial de
   riegos).
2. **Abstraccion del sensor**: interfaz `SensorInterface` con dos
   implementaciones — `MockDracalSensor` (desarrollo/tests) y
   `DracalPTHSensor` (real, via `dracal-usb-get`) — para que el resto de
   la app nunca dependa de si el hardware esta conectado.
3. **Logica de dominio separada**: `app/plants/advisor.py` traduce una
   lectura + un perfil de planta en una recomendacion de riego
   (si regar, por que, cuantos litros), testeable sin HTTP.
4. **3 endpoints obligatorios** en `routers/readings.py`, sin logica de
   negocio embebida (delegan a `advisor.py` y al sensor).
5. **Endpoints de soporte**: `plants` (perfiles) e `irrigation` (activar
   riego simulado), fuera del conteo de los 3 casos de uso pero
   necesarios para que el flujo completo tenga sentido.
6. **Frontend**: dashboard React que consume los 3 endpoints, con
   ilustracion SVG original, gauge de humedad, tarjeta de recomendacion,
   y grafica de historico con Recharts.
7. **Riesgo identificado y decision**: el Dracal mide humedad de aire,
   no de sustrato. Decision: documentarlo explicitamente en vez de
   presentar el dato como humedad de tierra (ver `CLAUDE.md`,
   restricciones).
8. **Orden de implementacion**: modelos -> sensor mock -> advisor ->
   endpoints obligatorios + tests -> endpoints de soporte -> frontend.

## Por que Plan Mode importa aqui

El paso 7 (la limitacion del sensor) solo se detecto al planificar antes
de escribir codigo — si se hubiera empezado directo por la UI, el
dashboard probablemente habria mostrado "humedad del suelo" de forma
enganosa. Este es exactamente el tipo de decision que Plan Mode ayuda a
capturar antes de la implementacion.

## Como generar tu propia evidencia de Plan Mode

1. Abre Claude Code en la raiz del repo.
2. Antes de pedir una funcionalidad no trivial, escribe explicitamente
   "entra en plan mode" (o usa el atajo de tu version de Claude Code).
3. Deja que Claude Code proponga el plan, ajustalo con tus comentarios,
   y **copia el plan final aprobado** a un archivo nuevo en `evidence/`
   (por ejemplo `evidence/plan-<feature>.md`) antes de aprobar la
   ejecucion.
