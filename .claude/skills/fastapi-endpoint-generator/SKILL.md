---
name: fastapi-endpoint-generator
description: Genera el andamiaje (schema Pydantic, router FastAPI, y test pytest) para un nuevo recurso REST en el backend de HidroMacetero, siguiendo las convenciones del proyecto (docstrings en espanol, comentarios estilo XML en clases de dominio, TDD). Usar cuando se pida agregar un nuevo endpoint o recurso al backend, por ejemplo "agrega un endpoint para X".
---

# Generador de endpoints FastAPI (HidroMacetero)

Este skill estandariza como se agrega un recurso nuevo al backend, para
que cada endpoint del proyecto tenga la misma forma: schema tipado, router
delgado, logica de dominio separada si aplica, y un test que se escribe
**antes** de la implementacion (ver tema "Test-driven Iteration" de la
asignacion).

## Cuando usarlo

- El usuario pide un endpoint nuevo ("agrega un endpoint para exportar el
  historial en CSV", "necesito un endpoint de estadisticas diarias", etc.)
- Se necesita un recurso CRUD adicional similar a `plants` o `readings`.

## Pasos a seguir (en orden)

1. **Definir el contrato primero.** Antes de escribir codigo, resume en
   una linea: metodo HTTP, path, request body (si aplica), response
   shape. Si el alcance no es trivial, pasa por Plan Mode.

2. **Escribir el test primero** en `backend/tests/test_<recurso>.py`,
   usando el fixture `client` de `conftest.py` (ya fuerza
   `SENSOR_MODE=mock` y una base SQLite en memoria con `StaticPool`).
   Ejemplo minimo:

   ```python
   def test_create_<recurso>_returns_201(client):
       response = client.post("/<recurso>", json={...})
       assert response.status_code == 201
   ```

   Corre `pytest -q` y confirma que falla (404 o error de import) antes
   de continuar.

3. **Agregar el schema** en `backend/app/schemas.py`: una clase
   `<Recurso>Create` (input) y `<Recurso>Out` (output, con
   `model_config = ConfigDict(from_attributes=True)` si mapea un modelo
   SQLAlchemy).

4. **Agregar el modelo** en `backend/app/models.py` si el recurso
   necesita persistencia, con un docstring de clase estilo XML:

   ```python
   class NuevoRecurso(Base):
       """
       /// <summary>
       /// Descripcion breve del recurso y su rol en el dominio.
       /// </summary>
       """
   ```

5. **Crear el router** en `backend/app/routers/<recurso>.py` siguiendo el
   patron de `plants.py` (CRUD simple) o `readings.py` (logica con
   dependencias de sensor/dominio):
   - Usa `APIRouter(prefix="/<recurso>", tags=["<recurso>"])`.
   - Inyecta `db: Session = Depends(get_db)`.
   - Usa `HTTPException(status_code=404, ...)` para recursos no
     encontrados, nunca dejes que una excepcion cruda llegue al cliente.

6. **Registrar el router** en `backend/app/main.py`:
   `app.include_router(<recurso>.router)`.

7. **Correr `pytest -q`** de nuevo y confirmar que el test ahora pasa.
   Actualizar `evidence/tdd-cycle.md` si este es el ciclo que se quiere
   documentar como evidencia formal.

8. Si el endpoint es publico y maneja datos sensibles o acciona hardware
   (como `/irrigation/water`), pedir explicitamente una revision de
   seguridad (ver tema "Security" de la asignacion) antes de darlo por
   terminado.

## Convenciones a respetar siempre

- Docstrings y comentarios en espanol; nombres de variables/funciones en
  ingles.
- No dupliques logica de negocio en el router: si el calculo es no
  trivial, sacalo a un modulo de dominio (como `app/plants/advisor.py`)
  para poder testearlo sin HTTP.
- Todo endpoint nuevo debe funcionar con `SENSOR_MODE=mock`, sin asumir
  hardware conectado.
