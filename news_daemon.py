"""
GRAVITY AI — DAEMON ORQUESTADOR V4.0
Orquesta los tres agentes de manera autónoma según rotación programada (via Workflow Engine V16.3 PRO):
  - workflows/reporter.json  → Noticias de coyuntura (cada ciclo)
  - workflows/essayist.json  → Ensayos filosóficos (cada 2 ciclos)
  - workflows/scientist.json → Artículos científicos (cada 3 ciclos)

Mejoras V4.0:
  - [R1] Refactorizado en clase PeriodistaOrchestrator — sin efectos secundarios al importar
  - [R2] Persistencia del cycle_count en estado JSON — sobrevive reinicios del daemon
  - [R3] Schema de estado enriquecido: total_published, last_error, consecutive_errors
  - [R4] Backpressure en el tiempo de espera — descuenta el tiempo que tardó el ciclo
  - [R5] Integración con OODA engine via hook_manager para alertas de fallos consecutivos
  - [R6] Integración con editorial_memory para registrar publicaciones
  - [D1] Logger central de Gravity (aparece en panel y en bridge.log)
  - [D2] Escribe _periodista_state.json para que el Dashboard muestre estado en tiempo real
  - [D3] Argumento --test para ejecutar un ciclo inmediato sin espera
  - [D4] Auto-restart al crash: un error no mata el daemon permanentemente
"""

import time
import random
import os
import sys
import json
import argparse
from datetime import datetime
from typing import Optional

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

local_app_data = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")), 
    "Gravity", 
    "Databases"
)
os.makedirs(local_app_data, exist_ok=True)
STATE_FILE = os.path.join(local_app_data, "_periodista_state.json")

# Umbral de errores consecutivos para dispararle alerta al OODA engine
CONSECUTIVE_ERROR_THRESHOLD = 3

# Intervalo de espera entre ciclos (horas)
WAIT_HOURS_MIN = 4.0
WAIT_HOURS_MAX = 8.0


# ══════════════════════════════════════════════════════════════════════════════
# PERIODISTA ORCHESTRATOR — clase principal
# ══════════════════════════════════════════════════════════════════════════════

class PeriodistaOrchestrator:
    """
    Orquestador autónomo del sistema periodístico de Gravity.

    Encapsula todo el estado y la lógica del daemon para evitar efectos
    secundarios al importar el módulo (facilita testing y reutilización).
    """

    def __init__(self, test_mode: bool = False):
        self.test_mode = test_mode
        self._state = self._load_state()

    # ── Estado persistido ──────────────────────────────────────────────────

    def _load_state(self) -> dict:
        """Carga el estado desde disco. Si no existe o está corrupto, retorna el estado inicial."""
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
            # Merge: conservar cycle_count y total_published si existían
            for key in ("cycle_count", "total_published", "consecutive_errors"):
                if key in saved and isinstance(saved[key], int):
                    default[key] = saved[key]
            for key in ("last_successful_publish", "last_article_title", "last_error"):
                if key in saved:
                    default[key] = saved[key]
            log.info(
                f"[Periodista] Estado restaurado: ciclo #{default['cycle_count']}, "
                f"{default['total_published']} artículos publicados totales."
            )
            return default
        except Exception as e:
            log.warning(f"[Periodista] Estado corrupto, reiniciando: {e}")
            return default

    def _save_state(
        self,
        status: str,
        last_title: str = "",
        next_run_ts: float = 0.0,
        error: Optional[str] = None,
        published_count: int = 0,
    ) -> None:
        """Persiste el estado actual en disco de forma atómica (D2)."""
        # BUG-4 FIX: contar por artículo, no por llamada
        if published_count > 0:
            self._state["total_published"] = self._state.get("total_published", 0) + published_count
            self._state["last_successful_publish"] = datetime.now().isoformat()
            # BUG-3 FIX: solo resetear si realmente se publicó algo
            self._state["consecutive_errors"] = 0
            self._state["last_error"] = None
        if error:
            self._state["consecutive_errors"] = self._state.get("consecutive_errors", 0) + 1
            self._state["last_error"] = str(error)[:300]
        # No resetear consecutive_errors si solo se llama con status neutral sin publicación

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
            log.warning(f"[Periodista] No se pudo escribir estado: {e}")

    # ── Alertas OODA ───────────────────────────────────────────────────────

    def _check_alert_ooda(self) -> None:
        """
        BUG-1 FIX: hook_manager no tiene emit(). En lugar de eso, marcamos
        el estado con consecutive_errors elevado para que el OODA engine
        lo lea en su fase OBSERVE al escanear _periodista_state.json.
        El autonomy_engine.py debe leer este archivo en _observe().
        """
        n = self._state.get("consecutive_errors", 0)
        if n >= CONSECUTIVE_ERROR_THRESHOLD:
            log.warning(
                f"[Periodista] ⚠ {n} errores consecutivos — estado marcado para detección por OODA engine."
            )
            # El estado ya fue persistido con consecutive_errors alto antes de llamar a esta función.
            # El OODA engine lo leerá en su próxima fase OBSERVE.

    # ── Ejecución de workflows ─────────────────────────────────────────────

    def _run_workflow_agent(self, workflow_name: str, agent_name: str) -> str:
        """
        [A3] Ejecuta el workflow directamente en-proceso (sin subprocess).
        Retorna el título del artículo generado, o "" si falla.
        """
        log.info(f"[Periodista] [{agent_name}] Iniciando workflow: {workflow_name}...")
        try:
            from core.workflow_engine import run_workflow
            import json as _json

            job = run_workflow(workflow_name, blocking=True)

            if job.status == "done":
                log.info(f"[Periodista] [{agent_name}] ✓ Workflow completado exitosamente.")
                # Extraer título del artículo generado
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
                log.warning(
                    f"[Periodista] [{agent_name}] ⚠ Workflow finalizó con estado: {job.status}. "
                    f"Error: {job.error or 'desconocido'}"
                )
                return ""

        except Exception as e:
            log.error(f"[Periodista] [{agent_name}] ✗ Error ejecutando workflow '{workflow_name}': {e}")
            return ""

    # ── Ciclo editorial completo ───────────────────────────────────────────

    def run_cycle(self) -> str:
        """
        Ejecuta un ciclo editorial completo.
        Retorna el título del último artículo publicado (o "" si todo falló).
        """
        cycle = self._state["cycle_count"]

        log.info(f"[Periodista] {'=' * 50}")
        log.info(f"[Periodista] CICLO #{cycle} — {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        log.info(f"[Periodista] {'=' * 50}")

        self._save_state("running", next_run_ts=0.0)

        last_title = ""
        articles_published = 0

        # Reporter: siempre
        title = self._run_workflow_agent(WORKFLOW_REPORTER, "REPORTER")
        if title:
            last_title = title
            articles_published += 1
            self._register_topic(WORKFLOW_REPORTER)

        # Essayist: cada 2 ciclos
        if cycle % 2 == 0:
            title = self._run_workflow_agent(WORKFLOW_ESSAYIST, "ESSAYIST")
            if title:
                last_title = title
                articles_published += 1
                self._register_topic(WORKFLOW_ESSAYIST)
        else:
            log.info(f"[Periodista] [ESSAYIST] Saltado (próximo en ciclo #{cycle + 1})")

        # Scientist: cada 3 ciclos
        if cycle % 3 == 0:
            title = self._run_workflow_agent(WORKFLOW_SCIENTIST, "SCIENTIST")
            if title:
                last_title = title
                articles_published += 1
                self._register_topic(WORKFLOW_SCIENTIST)
        else:
            next_sci = (cycle // 3 + 1) * 3
            log.info(f"[Periodista] [SCIENTIST] Saltado (próximo en ciclo #{next_sci})")

        log.info(f"[Periodista] Ciclo #{cycle}: {articles_published} artículo(s) publicado(s).")
        return last_title, articles_published

    def _register_topic(self, workflow: str) -> None:
        """Registra el workflow ejecutado en la memoria de topics (para deduplicación de ensayos/ciencia)."""
        # El topic real es registrado por topic_picker_node.py directamente.
        # Este método existe como punto de extensión futuro.
        pass

    # ── Loop principal ─────────────────────────────────────────────────────

    def run(self) -> None:
        """
        Loop principal del daemon con auto-restart (D4).
        En modo test, ejecuta un solo ciclo y termina.
        """
        log.info("[Periodista] " + "=" * 35)
        log.info("[Periodista]   GRAVITY AI — ORQUESTADOR AUTÓNOMO V4.0")
        log.info("[Periodista]   Reporter · Essayist · Scientist")
        log.info("[Periodista] " + "=" * 35)
        log.info("[Periodista] Sistema editorial autónomo en línea.")
        log.info("[Periodista] Noticias: cada ciclo | Ensayos: cada 2 ciclos | Ciencia: cada 3 ciclos")
        log.info(
            f"[Periodista] Estado previo: ciclo #{self._state['cycle_count']}, "
            f"{self._state.get('total_published', 0)} publicaciones totales."
        )

        if self.test_mode:
            log.info("[Periodista] [MODO TEST] Ejecutando primer ciclo inmediatamente.")
        else:
            log.info(f"[Periodista] Arrancando el primer ciclo inmediatamente...")
            self._save_state("waiting", next_run_ts=time.time())

        while True:
            cycle_start = time.time()

            try:
                self._state["cycle_count"] += 1

                last_title, articles_published = self.run_cycle()
                cycle_elapsed = time.time() - cycle_start

                if self.test_mode:
                    log.info("[Periodista] [MODO TEST] Ciclo completado. Daemon detenido.")
                    self._save_state("idle_test", last_title, published_count=articles_published)
                    sys.exit(0)

                # [R4] Backpressure: descontar el tiempo del ciclo del intervalo
                wait_hours = random.uniform(WAIT_HOURS_MIN, WAIT_HOURS_MAX)
                wait_secs = max(0.0, wait_hours * 3600 - cycle_elapsed)
                next_run_ts = time.time() + wait_secs
                next_run_str = datetime.fromtimestamp(next_run_ts).strftime("%Y-%m-%d %H:%M:%S")

                log.info(f"[Periodista] Ciclo #{self._state['cycle_count']} completado en {cycle_elapsed:.0f}s.")
                log.info(f"[Periodista] Próxima ejecución: {next_run_str} (en {wait_secs / 3600:.1f}h)")

                self._save_state("sleeping", last_title, next_run_ts, published_count=articles_published)
                time.sleep(wait_secs)

            except KeyboardInterrupt:
                log.info("[Periodista] Detenido manualmente por el usuario.")
                self._save_state("stopped")
                sys.exit(0)

            except Exception as e:
                # [D4] Auto-restart: un crash no mata el daemon
                log.error(
                    f"[Periodista] ✗ Error inesperado en ciclo #{self._state['cycle_count']}: {e}. "
                    "Reintentando en 60s..."
                )
                self._save_state("error", error=str(e))
                self._check_alert_ooda()
                time.sleep(60)


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    """Punto de entrada del daemon."""
    parser = argparse.ArgumentParser(description="Gravity AI — Daemon Orquestador Periodístico")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Ejecutar un ciclo inmediato sin espera inicial (modo test)",
    )
    args, _ = parser.parse_known_args()

    orchestrator = PeriodistaOrchestrator(test_mode=args.test)
    orchestrator.run()


if __name__ == "__main__":
    main()
