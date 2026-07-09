"""
tests/test_scheduler.py

Ciclo TDD (ver evidence/tdd-cycle.md, segundo ciclo): estos tests se
escribieron ANTES de que existiera app/scheduler.py, para guiar el
guardado automatico y periodico de lecturas (APScheduler corriendo
dentro de la app FastAPI).
"""
import pytest

from app import scheduler


@pytest.fixture(autouse=True)
def _reset_scheduler_singleton():
    scheduler.stop_scheduler()
    yield
    scheduler.stop_scheduler()


def test_interval_minutes_default_is_15(monkeypatch):
    monkeypatch.delenv("AUTO_SAVE_INTERVAL_MINUTES", raising=False)
    assert scheduler._interval_minutes() == 15


def test_interval_minutes_uses_custom_value(monkeypatch):
    monkeypatch.setenv("AUTO_SAVE_INTERVAL_MINUTES", "5")
    assert scheduler._interval_minutes() == 5


def test_interval_minutes_falls_back_on_invalid_value(monkeypatch):
    monkeypatch.setenv("AUTO_SAVE_INTERVAL_MINUTES", "no-es-un-numero")
    assert scheduler._interval_minutes() == 15


def test_interval_minutes_falls_back_on_non_positive_value(monkeypatch):
    monkeypatch.setenv("AUTO_SAVE_INTERVAL_MINUTES", "0")
    assert scheduler._interval_minutes() == 15


def test_is_enabled_default_true(monkeypatch):
    monkeypatch.delenv("AUTO_SAVE_ENABLED", raising=False)
    assert scheduler._is_enabled() is True


@pytest.mark.parametrize("value", ["false", "False", "0", "no", "off"])
def test_is_enabled_false_variants(monkeypatch, value):
    monkeypatch.setenv("AUTO_SAVE_ENABLED", value)
    assert scheduler._is_enabled() is False


@pytest.mark.parametrize("value", ["true", "True", "1", "yes", "on"])
def test_is_enabled_true_variants(monkeypatch, value):
    monkeypatch.setenv("AUTO_SAVE_ENABLED", value)
    assert scheduler._is_enabled() is True


def test_start_scheduler_disabled_does_nothing(monkeypatch):
    monkeypatch.setenv("AUTO_SAVE_ENABLED", "false")
    scheduler.start_scheduler()
    assert scheduler._scheduler is None
    scheduler.stop_scheduler()  # no debe lanzar aunque nunca arranco


def test_start_scheduler_enabled_starts_and_stops(monkeypatch):
    monkeypatch.setenv("AUTO_SAVE_ENABLED", "true")
    monkeypatch.setenv("AUTO_SAVE_INTERVAL_MINUTES", "15")
    scheduler.start_scheduler()
    assert scheduler._scheduler is not None
    assert scheduler._scheduler.running is True

    scheduler.stop_scheduler()
    assert scheduler._scheduler is None
