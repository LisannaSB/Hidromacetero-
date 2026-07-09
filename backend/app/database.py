"""
database.py
Configuracion de SQLAlchemy + SQLite para HidroMacetero.

Convencion del proyecto (ver CLAUDE.md): una unica base SQLite local
'hidromacetero.db' en la raiz de /backend, sin migraciones (Alembic)
por estar fuera del alcance de esta asignacion.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./hidromacetero.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """Dependencia de FastAPI: entrega una sesion y garantiza su cierre."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
