"""
tests/conftest.py

Fixtures compartidas: usa una base SQLite en memoria (aislada de
hidromacetero.db) y fuerza SENSOR_MODE=mock para que los tests nunca
dependan del hardware Dracal fisico.
"""
import os

os.environ["SENSOR_MODE"] = "mock"
os.environ["AUTO_SAVE_ENABLED"] = "false"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app
from app.sensor import reset_sensor, reset_sensor_cache

TEST_DATABASE_URL = "sqlite:///:memory:"


@pytest.fixture(autouse=True)
def _reset_sensors():
    reset_sensor()
    reset_sensor_cache()
    yield


@pytest.fixture()
def db_session():
    # StaticPool: una unica conexion compartida para que la base en
    # memoria persista entre queries dentro del mismo test.
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
