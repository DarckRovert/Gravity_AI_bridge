"""
GRAVITY AI — DAEMON ORQUESTADOR V3.0
Orquesta los tres agentes de manera autónoma según rotación programada (via Workflow Engine V16.3 PRO):
  - workflows/reporter.json  → Noticias de coyuntura (cada ciclo)
  - workflows/essayist.json  → Ensayos filosóficos (cada 2 ciclos)
  - workflows/scientist.json → Artículos científicos (cada 3 ciclos)

Mejoras V3.0:
  - [A3] Llama al WorkflowEngine en-proceso (sin subprocess) — 30-60s más rápido, menos RAM
  - [D1] Usa el logger central de Gravity (aparece en el panel y en bridge.log)
  - [D2] Escribe _periodista_state.json para que el Dashboard muestre el estado en tiempo real
  - [D3] Argumento --test para ejecutar un ciclo inmediato sin espera de 10 minutos
  - [D4] Auto-restart al crash: un error no mata el daemon permanentemente
"""

import time
import random
import os
import sys
import json
import argparse
from datetime import datetime

# ── Configuración de codificación UTF-8 ────────────────────────────────────────
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# ── Logger central de Gravity (D1) ────────────────────────────────────────────
try:
    from core.logger import log
except ImportError:
    import logging
    log = logging.getLogger("periodista")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

WORKFLOW_REPORTER = "reporter"
WORKFLOW_ESSAYIST = "essayist"
WORKFLOW_SCIENTIST = "scientist"

STATE_FILE = os.path.join(BASE_DIR, "_periodista_state.json")

# ── Argumento --test (D3) ──────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Gravity AI — Daemon Orquestador Periodístico")
parser.add_argument("--test", action="store_true", help="Ejecutar un ciclo inmediato sin espera inicial (modo test)")
args, _ = parser.parse_known_args()


def _write_state(status: str, cycle: int, last_title: str = "", next_run_ts: float = 0.0):
    """Escribe el estado actual del Periodista a disco para que el Dashboard lo lea (D2)."""
    try:
        state = {
            "status": status,
            "cycle_count": cycle,
            "last_article_title": last_title,
            "last_run": datetime.now().isoformat(),
            "next_run": datetime.fromtimestamp(next_run_ts).isoformat() if next_run_ts > 0 else "",
            "next_run_ts": next_run_ts,
        }
        tmp = STATE_FILE + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
        os.replace(tmp, STATE_FILE)
    except Exception as e:
        log.warning(f"[Periodista] No se pudo escribir estado: {e}")


def run_workflow_agent(workflow_name: str, agent_name: str) -> str:
    """
    [A3] Ejecuta el workflow directamente en-proceso (sin subprocess).
    Retorna el título del artículo generado, o "" si falla.
    """
    log.info(f"[Periodista] [{agent_name}] Iniciando workflow: {workflow_name}...")
    try:
        from core.workflow_engine import run_workflow

        job = run_workflow(workflow_name, blocking=True)

        if job.status == "done":
            log.info(f"[Periodista] [{agent_name}] ✓ Workflow completado exitosamente.")
            # Intentar extraer el título del artículo para el estado
            # El nodo normalizador puede llamarse normalizar_noticia / normalizar_ensayo / normalizar_ciencia
            try:
                all_outputs = job.outputs.get("_all_node_outputs", {})
                title = ""
                for node_id, node_out in all_outputs.items():
                    if node_id.startswith("normalizar_") and isinstance(node_out, dict):
                        norm_json = node_out.get("normalized_json", "{}")
                        title = json.loads(norm_json).get("title", "")
                        if title:
                            break
                return title
            except Exception:
                return ""
        else:
            log.warning(f"[Periodista] [{agent_name}] ⚠ Workflow finalizó con estado: {job.status}. Error: {job.error or 'desconocido'}")
            return ""

    except Exception as e:
        log.error(f"[Periodista] [{agent_name}] ✗ Error ejecutando workflow '{workflow_name}': {e}")
        return ""


def run_cycle(cycle_count: int) -> str:
    """Ejecuta un ciclo editorial completo. Retorna el título del último artículo."""
    log.info(f"[Periodista] {'='*50}")
    log.info(f"[Periodista] CICLO #{cycle_count} — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    log.info(f"[Periodista] {'='*50}")

    _write_state("running", cycle_count)

    last_title = ""

    # Reporter: siempre
    last_title = run_workflow_agent(WORKFLOW_REPORTER, "REPORTER") or last_title

    # Essayist: cada 2 ciclos
    if cycle_count % 2 == 0:
        run_workflow_agent(WORKFLOW_ESSAYIST, "ESSAYIST")
    else:
        log.info(f"[Periodista] [ESSAYIST] Saltado este ciclo (próximo en ciclo #{cycle_count + 1})")

    # Scientist: cada 3 ciclos
    if cycle_count % 3 == 0:
        run_workflow_agent(WORKFLOW_SCIENTIST, "SCIENTIST")
    else:
        next_science = (cycle_count // 3 + 1) * 3
        log.info(f"[Periodista] [SCIENTIST] Saltado este ciclo (próximo en ciclo #{next_science})")

    return last_title


# ── Main loop con auto-restart al crash (D4) ──────────────────────────────────
log.info("[Periodista] =" * 35)
log.info("[Periodista]   GRAVITY AI — ORQUESTADOR AUTÓNOMO V3.0")
log.info("[Periodista]   Reporter · Essayist · Scientist")
log.info("[Periodista] =" * 35)
log.info("[Periodista] Sistema editorial autónomo en línea.")
log.info("[Periodista] Noticias: cada ciclo | Ensayos: cada 2 ciclos | Ciencia: cada 3 ciclos")

if args.test:
    log.info("[Periodista] [MODO TEST] Ejecutando primer ciclo inmediatamente (sin espera).")
else:
    wait_mins = 10
    log.info(f"[Periodista] Primera ejecución en {wait_mins} minutos...")
    _write_state("waiting", 0, next_run_ts=time.time() + wait_mins * 60)
    time.sleep(wait_mins * 60)

cycle_count = 0

while True:
    try:
        cycle_count += 1

        last_title = run_cycle(cycle_count)

        # Calcular próxima ejecución (entre 4 y 8 horas)
        if args.test:
            log.info("[Periodista] [MODO TEST] Ciclo de prueba completado. Daemon detenido.")
            _write_state("idle_test", cycle_count, last_title)
            sys.exit(0)

        wait_hours = random.uniform(4, 8)
        next_run_ts = time.time() + (wait_hours * 3600)
        next_run_str = datetime.fromtimestamp(next_run_ts).strftime("%Y-%m-%d %H:%M:%S")

        log.info(f"[Periodista] Ciclo #{cycle_count} completado.")
        log.info(f"[Periodista] Próxima ejecución: {next_run_str} (en {wait_hours:.1f}h)")

        _write_state("sleeping", cycle_count, last_title, next_run_ts)
        time.sleep(wait_hours * 3600)

    except KeyboardInterrupt:
        log.info("[Periodista] Detenido manualmente por el usuario.")
        _write_state("stopped", cycle_count)
        sys.exit(0)

    except Exception as e:
        # [D4] Auto-restart: un crash no mata el daemon
        log.error(f"[Periodista] ✗ Error inesperado en ciclo #{cycle_count}: {e}. Reintentando en 60s...")
        _write_state("error", cycle_count)
        time.sleep(60)
        # El while True reinicia el ciclo automáticamente
