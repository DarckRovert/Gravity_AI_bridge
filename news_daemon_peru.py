"""
GRAVITY AI — DAEMON ORQUESTADOR (SKIN PERÚ)
Orquesta únicamente al reportero de Perú de forma autónoma.
"""

import time
import random
import os
import sys
import json
import argparse
import tempfile
from datetime import datetime
from typing import Optional
import warnings

# Ocultar advertencias no críticas
warnings.filterwarnings("ignore", category=UserWarning, module="onnxruntime")

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

try:
    from core.logger import log
except ImportError:
    import logging
    log = logging.getLogger("periodista_peru")
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

WORKFLOW_REPORTER = "reporter_peru"

local_app_data = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")), 
    "Gravity", 
    "Databases"
)
os.makedirs(local_app_data, exist_ok=True)
STATE_FILE = os.path.join(local_app_data, "_periodista_peru_state.json")

CONSECUTIVE_ERROR_THRESHOLD = 3
WAIT_HOURS_MIN = 0.5
WAIT_HOURS_MAX = 1.0


class PeriodistaPeruOrchestrator:
    def __init__(self, test_mode: bool = False):
        self.test_mode = test_mode
        self._state = self._load_state()

    def _load_state(self) -> dict:
        default = {
            "status": "init",
            "cycle_count": 0,
            "total_published": 0,
            "last_successful_publish": None,
            "last_error": None,
            "consecutive_errors": 0,
            "last_article_title": "",
            "last_run": None,
            "next_run": None,
            "next_run_ts": 0.0,
        }
        if not os.path.isfile(STATE_FILE):
            return default
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            for key in ("cycle_count", "total_published", "consecutive_errors"):
                if key in saved and isinstance(saved[key], int):
                    default[key] = saved[key]
            for key in ("last_successful_publish", "last_article_title", "last_error"):
                if key in saved:
                    default[key] = saved[key]
            log.info(
                f"[Periodista Perú] Estado restaurado: ciclo #{default['cycle_count']}, "
                f"{default['total_published']} artículos publicados."
            )
            return default
        except Exception as e:
            log.warning(f"[Periodista Perú] Estado corrupto, reiniciando: {e}")
            return default

    def _save_state(
        self,
        status: str,
        last_title: str = "",
        next_run_ts: float = 0.0,
        error: Optional[str] = None,
        published_count: int = 0,
    ) -> None:
        if published_count > 0:
            self._state["total_published"] = self._state.get("total_published", 0) + published_count
            self._state["last_successful_publish"] = datetime.now().isoformat()
            self._state["consecutive_errors"] = 0
            self._state["last_error"] = None
        if error:
            self._state["consecutive_errors"] = self._state.get("consecutive_errors", 0) + 1
            self._state["last_error"] = str(error)[:300]

        self._state.update({
            "status": status,
            "last_run": datetime.now().isoformat(),
            "last_article_title": last_title or self._state.get("last_article_title", ""),
            "next_run": datetime.fromtimestamp(next_run_ts).isoformat() if next_run_ts > 0 else "",
            "next_run_ts": next_run_ts,
            "cycle_count": self._state.get("cycle_count", 0),
        })

        try:
            tmp = STATE_FILE + ".tmp"
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(self._state, f, indent=2, ensure_ascii=False)
            os.replace(tmp, STATE_FILE)
        except Exception as e:
            log.warning(f"[Periodista Perú] No se pudo escribir estado: {e}")

    def _run_workflow_agent(self, workflow_name: str, agent_name: str) -> str:
        log.info(f"[Periodista Perú] [{agent_name}] Iniciando workflow: {workflow_name}...")
        try:
            from core.workflow_engine import run_workflow
            import json as _json

            job = run_workflow(workflow_name, params={}, blocking=True)

            if job.status == "done":
                log.info(f"[Periodista Perú] [{agent_name}] ✓ Workflow completado exitosamente.")
                try:
                    all_outputs = job.outputs.get("_all_node_outputs", {})
                    title = ""
                    for node_id, node_out in all_outputs.items():
                        if node_id.startswith("normalizar_") and isinstance(node_out, dict):
                            norm_json = node_out.get("normalized_json", "{}")
                            title = _json.loads(norm_json).get("title", "")
                            if title:
                                break
                    return title
                except Exception:
                    return ""
            else:
                log.warning(f"[Periodista Perú] [{agent_name}] ⚠ Workflow falló: {job.status}.")
                return ""

        except Exception as e:
            log.error(f"[Periodista Perú] [{agent_name}] ✗ Error ejecutando workflow '{workflow_name}': {e}")
            return ""

    def run_cycle(self) -> str:
        cycle = self._state["cycle_count"]
        log.info(f"[Periodista Perú] {'=' * 50}")
        log.info(f"[Periodista Perú] CICLO #{cycle} — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log.info(f"[Periodista Perú] {'=' * 50}")

        self._save_state("running", next_run_ts=0.0)
        last_title = ""
        articles_published = 0

        title = self._run_workflow_agent(WORKFLOW_REPORTER, "REPORTER_PERU")
        if title:
            last_title = title
            articles_published += 1

        log.info(f"[Periodista Perú] Ciclo #{cycle}: {articles_published} artículo(s) publicado(s).")
        return last_title, articles_published

    def run(self) -> None:
        log.info("[Periodista Perú] " + "=" * 35)
        log.info("[Periodista Perú]   GRAVITY AI — ORQUESTADOR PERÚ")
        log.info("[Periodista Perú] " + "=" * 35)

        if self.test_mode:
            log.info("[Periodista Perú] [MODO TEST] Ejecutando primer ciclo inmediatamente.")
        else:
            log.info(f"[Periodista Perú] Arrancando el primer ciclo inmediatamente...")
            self._save_state("waiting", next_run_ts=time.time())

        while True:
            cycle_start = time.time()
            try:
                self._state["cycle_count"] += 1
                last_title, articles_published = self.run_cycle()
                cycle_elapsed = time.time() - cycle_start

                if self.test_mode:
                    self._save_state("idle_test", last_title, published_count=articles_published)
                    sys.exit(0)

                wait_hours = random.uniform(WAIT_HOURS_MIN, WAIT_HOURS_MAX)
                wait_secs = max(0.0, wait_hours * 3600 - cycle_elapsed)
                next_run_ts = time.time() + wait_secs
                
                log.info(f"[Periodista Perú] Próxima ejecución en {wait_secs / 3600:.1f}h")
                self._save_state("sleeping", last_title, next_run_ts, published_count=articles_published)
                
                import gc
                gc.collect()
                time.sleep(wait_secs)

            except KeyboardInterrupt:
                self._save_state("stopped")
                sys.exit(0)
            except Exception as e:
                log.error(f"[Periodista Perú] ✗ Error: {e}. Reintentando en 60s...")
                self._save_state("error", error=str(e))
                time.sleep(60)

def main() -> None:
    if sys.platform == "win32":
        import msvcrt
        lock_file = os.path.join(tempfile.gettempdir(), "gravity_periodista_peru.lock")
        global_lock_fd = os.open(lock_file, os.O_CREAT | os.O_RDWR)
        try:
            msvcrt.locking(global_lock_fd, msvcrt.LK_NBLCK, 1)
        except IOError:
            print("[!] GRAVITY AI: El Reportero Perú ya está en ejecución (Lock activo).")
            sys.exit(1)

    parser = argparse.ArgumentParser(description="Gravity AI — Reportero Perú")
    parser.add_argument("--test", action="store_true")
    args, _ = parser.parse_known_args()

    orchestrator = PeriodistaPeruOrchestrator(test_mode=args.test)
    orchestrator.run()

if __name__ == "__main__":
    main()
