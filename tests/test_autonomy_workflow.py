import os
import sys

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from core.autonomy_engine import _execute_low_risk_action
from core.workflow_engine import list_jobs
import time

def run_tests():
    print("=== Testing Autonomy Engine -> Workflow Engine ===")

    mock_action = {
        "risk": "BAJA",
        "module": "workflow_engine",
        "description": 'run_workflow("investigacion_rapida", {"topic": "Computación Cuántica"})'
    }

    print(f"\n[*] Ejecutando accion simulada del LLM:")
    print(f"    Modulo: {mock_action['module']}")
    print(f"    Desc: {mock_action['description']}")

    ok, result = _execute_low_risk_action(mock_action)
    print(f"\n[*] Respuesta del handler:")
    print(f"    OK: {ok}")
    print(f"    MSG: {result}")

    if not ok:
        print("[!] Test falló.")
        return

    # Extract Job ID
    import re
    m = re.search(r"Job ([a-z0-9]+)", result)
    if not m:
        print("[!] No se encontró el Job ID en la respuesta.")
        return

    job_id = m.group(1)
    
    # Wait for completion
    print(f"\n[*] Esperando a que el Job {job_id} termine (background thread)...")
    
    from core.workflow_engine import get_job
    job = get_job(job_id)
    
    while job.status in ["pending", "running"]:
        time.sleep(1)
        job = get_job(job_id)
        sys.stdout.write(".")
        sys.stdout.flush()

    print(f"\n\n[*] Job {job.job_id} terminado con estado: {job.status}")
    if job.status == "done":
        print(f"    Outputs: {list(job.outputs.keys())}")
    elif job.status == "failed":
        print(f"    Error: {job.error}")

    print("\n[✓] Test de integración completado.")

if __name__ == "__main__":
    run_tests()
