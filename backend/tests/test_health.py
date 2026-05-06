"""
test_health.py — Testes da rota GET /health.

Verifica que o backend responde corretamente ao health check.
"""

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


def test_health_returns_200():
    """A rota /health deve retornar status HTTP 200."""
    response = client.get("/health")
    assert response.status_code == 200


def test_health_returns_status_ok():
    """A rota /health deve retornar JSON com {"status": "ok"}."""
    response = client.get("/health")
    assert response.json() == {"status": "ok"}
