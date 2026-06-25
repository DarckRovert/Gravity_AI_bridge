import os
import sys

# Setup path so we can import core
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from core.logger import log
from core.workflow_engine import run_workflow, get_job, list_workflows, list_nodes

def run_tests():
    print("=== Testing Workflow Engine ===")
    
    # 1. Test Listing Nodes
    nodes = list_nodes()
    print(f"[*] Registrados {len(nodes)} nodos:")
    for nt, nd in nodes.items():
        print(f"  - {nt}")

    # 2. Test Listing Workflows
    workflows = list_workflows()
    print(f"\n[*] Workflows encontrados: {len(workflows)}")
    for wf in workflows:
        print(f"  - {wf['workflow_id']} ({wf['node_count']} nodes)")

    # 3. Test simple workflow execution
    wf_id = "investigacion_rapida"
    print(f"\n[*] Ejecutando workflow de prueba: {wf_id}")
    
    # Check if workflow exists
    if not any(w['workflow_id'] == wf_id for w in workflows):
        print(f"[!] El workflow {wf_id} no fue encontrado para el test. Abortando.")
        return

    job = run_workflow(
        workflow_id=wf_id,
        params={"topic": "Inteligencia Artificial Agentica"},
        blocking=True
    )

    print(f"\n[*] Resultado final (Job {job.job_id}):")
    print(f"    Status: {job.status}")
    print(f"    Elapsed: {job.finished_at - job.started_at:.2f}s" if job.finished_at else "N/A")
    if job.error:
        print(f"    Error: {job.error}")
        
    print("\n[✓] Test completado.")

if __name__ == "__main__":
    run_tests()
