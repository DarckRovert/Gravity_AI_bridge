import subprocess
import time
import urllib.request
import json
import sys
import os

print("--- Iniciando prueba de Tinka API en servidor ---")

# Iniciar servidor
env = os.environ.copy()
env["PYTHONIOENCODING"] = "utf-8"
server_proc = subprocess.Popen([sys.executable, "bridge_server.py"], env=env)
print("Servidor iniciado. Esperando hasta 15 segundos para carga...")

base_url = "http://localhost:7860/v1/tinka"
errors = 0

# Wait for server to bind
server_up = False
for _ in range(15):
    try:
        urllib.request.urlopen("http://localhost:7860/health", timeout=2)
        server_up = True
        break
    except Exception:
        time.sleep(1)

if not server_up:
    print("[ERROR] El servidor no se levanto en el tiempo esperado.")
    server_proc.kill()
    sys.exit(1)

print("Servidor en linea. Ejecutando tests...")


def test_endpoint(name, url, method="GET"):
    global errors
    print(f"\n[TEST] Ejecutando: {name} ({url})")
    try:
        req = urllib.request.Request(url, method=method)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            print("[EXITO] Respuesta:")
            print(json.dumps(data, indent=2))
    except Exception as e:
        print(f"[ERROR]: {e}")
        errors += 1


try:
    test_endpoint("Status Inicial", f"{base_url}/status")
    test_endpoint("Generar Dummy Data", f"{base_url}/update?dummy=true")
    test_endpoint("Status Post-Update", f"{base_url}/status")
    test_endpoint("Analisis de Patrones", f"{base_url}/analyze")
    test_endpoint("Predecir Jugada", f"{base_url}/predict")
finally:
    print("\nCerrando servidor...")
    server_proc.terminate()
    try:
        server_proc.wait(timeout=5)
    except subprocess.TimeoutExpired:
        server_proc.kill()

    if errors == 0:
        print("\n[OK] TODOS LOS TESTS PASARON SIN ERRORES.")
    else:
        print(f"\n[FAIL] SE ENCONTRARON {errors} ERRORES.")
        sys.exit(1)
