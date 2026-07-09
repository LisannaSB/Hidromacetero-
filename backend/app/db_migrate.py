"""
db_migrate.py

Este proyecto NO usa Alembic (ver CLAUDE.md, restricciones) porque esta
fuera del alcance de la asignacion. Pero eso significa que si alguien ya
tenia una base `hidromacetero.db` creada ANTES de que existiera la tabla
`sensors`/columna `plants.sensor_id`, `Base.metadata.create_all()` no
altera tablas existentes -- solo crea las que faltan.

Esta funcion es un parche minimo y explicito (no un framework de
migraciones) que agrega esa columna si hace falta, para que quien ya
haya usado la app no tenga que borrar su base de datos.
"""
from sqlalchemy import inspect
from sqlalchemy.engine import Engine


def ensure_plant_sensor_column(engine: Engine) -> None:
    inspector = inspect(engine)
    if "plants" not in inspector.get_table_names():
        return  # tabla nueva, create_all ya la crea con la columna incluida

    columns = [col["name"] for col in inspector.get_columns("plants")]
    if "sensor_id" in columns:
        return  # ya esta al dia

    with engine.begin() as conn:
        conn.exec_driver_sql("ALTER TABLE plants ADD COLUMN sensor_id INTEGER")
