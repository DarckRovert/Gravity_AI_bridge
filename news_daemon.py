"""
GRAVITY AI — DAEMON ORQUESTADOR V2.0
Orquesta los tres agentes de manera autónoma según rotación programada (via Workflow Engine V16.3 PRO):
  - workflows/reporter.json  → Noticias de coyuntura (cada ciclo)
  - workflows/essayist.json  → Ensayos filosóficos (cada 2 ciclos)
  - workflows/scientist.json → Artículos científicos (cada 3 ciclos)
"""

import time
import subprocess
import random
import os
import sys
from datetime import datetime

# Forzar codificación UTF-8 para evitar errores con caracteres como ✓ o ✗
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

WORKFLOW_REPORTER = "reporter"
WORKFLOW_ESSAYIST = "essayist"
WORKFLOW_SCIENTIST = "scientist"


def banner():
    print("=" * 70)
    print("  GRAVITY AI — ORQUESTADOR AUTÓNOMO V2.0 (3 Agentes Activos)")
    print("  Reporter · Essayist · Scientist")
    print("=" * 70)
    print("[*] El sistema editorial autónomo está en línea.")
    print("[*] Noticias: cada ciclo | Ensayos: cada 2 ciclos | Ciencia: cada 3 ciclos")


def run_workflow_agent(workflow_name: str, agent_name: str):
    """Lanza un workflow como subproceso usando el motor autónomo V16.3 PRO."""
    print(
        f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] [{agent_name}] Iniciando Workflow: {workflow_name}..."
    )
    try:
        # Reemplaza la ejecución de scripts legacy por el motor de workflows
        cmd = [
            "python", "-c",
            f"import sys; sys.path.insert(0, r'{BASE_DIR}'); "
            f"from core.workflow_engine import run_workflow; "
            f"job = run_workflow('{workflow_name}', blocking=True); "
            f"sys.exit(0 if job.status == 'done' else 1)"
        ]
        result = subprocess.run(
            cmd,
            cwd=BASE_DIR,
            timeout=2700,  # 45 min máximo por agente (para tolerar la cascada completa de LLMs)
        )
        if result.returncode == 0:
            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] [{agent_name}] ✓ Completado exitosamente."
            )
        else:
            print(
                f"[{datetime.now().strftime('%H:%M:%S')}] [{agent_name}] ⚠ Finalizó con código {result.returncode}."
            )
    except subprocess.TimeoutExpired:
        print(
            f"[{datetime.now().strftime('%H:%M:%S')}] [{agent_name}] ✗ Timeout. El agente tardó más de 45 minutos (Cascada agotada)."
        )
    except Exception as e:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] [{agent_name}] ✗ Error: {e}")


banner()

# Primer ciclo arranca en 10 minutos para dar tiempo al usuario a ver actividad
is_first_run = True
cycle_count = 0

while True:
    if is_first_run:
        wait_mins = 10
        print(f"\n[*] Primera ejecución en {wait_mins} minutos...")
        time.sleep(wait_mins * 60)
        is_first_run = False

    cycle_count += 1
    print(f"\n{'='*50}")
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] CICLO #{cycle_count}")
    print(f"{'='*50}")

    # Reporter: siempre
    run_workflow_agent(WORKFLOW_REPORTER, "REPORTER")

    # Essayist: cada 2 ciclos
    if cycle_count % 2 == 0:
        run_workflow_agent(WORKFLOW_ESSAYIST, "ESSAYIST")
    else:
        print(
            f"[*] [ESSAYIST] Saltado en este ciclo (próxima vez en ciclo #{cycle_count + 1})"
        )

    # Scientist: cada 3 ciclos
    if cycle_count % 3 == 0:
        run_workflow_agent(WORKFLOW_SCIENTIST, "SCIENTIST")
    else:
        print(
            f"[*] [SCIENTIST] Saltado en este ciclo (próxima vez en ciclo #{(cycle_count // 3 + 1) * 3})"
        )

    # Calcular próxima ejecución (entre 4 y 8 horas)
    wait_hours = random.uniform(4, 8)
    next_run = datetime.fromtimestamp(time.time() + (wait_hours * 3600))
    print(f"\n[*] Ciclo #{cycle_count} completado.")
    print(
        f"[*] Próxima ejecución: {next_run.strftime('%Y-%m-%d %H:%M:%S')} (en {wait_hours:.1f}h)"
    )

    time.sleep(wait_hours * 3600)
