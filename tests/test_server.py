import pytest
import requests
import time
import subprocess
import os

# Nota: Estas pruebas requieren que el servidor esté corriendo
# Para propósitos de CI, se debería orquestar el inicio/fin del proceso.

BASE_URL = "http://localhost:7860"

@pytest.fixture(scope="module", autouse=True)
def ensure_server():
    # Intentar ver si ya está corriendo
    try:
        requests.get(f"{BASE_URL}/v1/status", timeout=1)
        yield
    except requests.exceptions.ConnectionError:
        # Aquí se podría lanzar el subproceso, pero para este entorno
        # asumimos que el usuario o el agente lo controla.
        pytest.skip("Servidor no detectado en localhost:7860")

def test_status_endpoint():
    r = requests.get(f"{BASE_URL}/v1/status")
    assert r.status_code == 200
    data = r.json()
    assert data["version"] == "8.0"
    assert "active_provider" in data

def test_models_endpoint():
    r = requests.get(f"{BASE_URL}/v1/models")
    assert r.status_code == 200
    data = r.json()
    assert "data" in data
    assert any(m["id"] == "gravity-bridge-auto" for m in data["data"])

def test_metrics_endpoint():
    r = requests.get(f"{BASE_URL}/metrics")
    assert r.status_code == 200
    assert "gravity_requests_total" in r.text

def test_audit_endpoint():
    r = requests.get(f"{BASE_URL}/v1/audit")
    assert r.status_code == 200
    data = r.json()
    assert "data" in data
