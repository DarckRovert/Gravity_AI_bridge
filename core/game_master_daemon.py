"""
=============================================================================
        GRAVITY AI — GAME MASTER AUTONOMOUS DAEMON V1.0 PRO
        Agente Autónomo de Creación de Eventos y Gestión de Servidor
=============================================================================
Daemon en segundo plano que ejecuta el ciclo OODA (Observe-Orient-Decide-Act)
sobre el servidor AzerothCore de WoW Perú:
  - Monitorea jugadores activos y liveness del servidor
  - Genera anuncios narrativos y de lore dinámico mediante el LLM activo
  - Lanza micro-eventos ambientales y recordatorios estacionales del BattlePass
  - Registra cada decisión en _audit_log.jsonl y _game_master_state.json
"""

import os
import sys
import time
import json
import random
import logging
import threading
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from core.logger import log
from core import game_server_manager, provider_manager
from tools.wow_server_tool import WoWServerTool

STATE_FILE = os.path.join(BASE_DIR, "_game_master_state.json")
AUDIT_FILE = os.path.join(BASE_DIR, "_audit_log.jsonl")


class GameMasterDaemon:
    """
    Agente Autónomo Game Master para WoW Perú.
    """

    def __init__(
        self,
        server_id: str = "wow_peru",
        interval_seconds: int = 1800,  # Cada 30 minutos por defecto
        lore_theme: str = "Reino Andino - Temporada 2: La Forja Andina",
    ) -> None:
        self.server_id = server_id
        self.interval = interval_seconds
        self.lore_theme = lore_theme
        self.running = False
        self._thread: Optional[threading.Thread] = None
        self.tool = WoWServerTool()
        self.cycle_count = 0
        self._load_state()

    def _load_state(self) -> None:
        """Carga el estado previo persistido."""
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.cycle_count = data.get("cycle_count", 0)
            except Exception:
                pass

    def _save_state(self, last_action: Dict[str, Any]) -> None:
        """Persiste el estado actual para observabilidad en el Dashboard."""
        data = {
            "cycle_count": self.cycle_count,
            "last_cycle": datetime.now(timezone.utc).isoformat(),
            "server_id": self.server_id,
            "lore_theme": self.lore_theme,
            "last_action": last_action,
        }
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            log.warning(f"[GameMaster] Error guardando estado: {e}")

    def _append_audit(self, entry: Dict[str, Any]) -> None:
        """Añade entrada al log de auditoría."""
        entry["timestamp"] = datetime.now(timezone.utc).isoformat()
        entry["agent"] = "GameMasterDaemon"
        try:
            with open(AUDIT_FILE, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            pass

    def step_observe(self) -> Dict[str, Any]:
        """FASE O: Observa el estado del servidor."""
        cmd_res = self.tool.execute(action="status", server=self.server_id)
        players_res = game_server_manager.get_players(self.server_id)
        return {
            "server_online": cmd_res.success,
            "server_output": cmd_res.stdout,
            "player_count": players_res.get("count", 0),
            "players": players_res.get("players", []),
        }

    def step_decide(self, observation: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """FASE D: El LLM evalúa la situación y genera una acción."""
        if not observation.get("server_online"):
            log.warning(f"[GameMaster] Servidor '{self.server_id}' no responde a SOAP. Omitiendo ciclo.")
            return None

        # Selección de tipo de acción
        action_types = ["announce_lore", "battlepass_reminder", "weather_or_trivia"]
        chosen_type = random.choice(action_types)

        prompt = (
            f"Eres el Game Master y narrador oficial de WoW Perú ({self.lore_theme}).\n"
            f"Jugadores conectados actualmente: {observation.get('player_count')}.\n"
            f"Tipo de mensaje a redactar: {chosen_type}.\n"
            "Instrucciones:\n"
            "- Redacta UN ÚNICO mensaje breve (máximo 120 caracteres) para el chat del juego.\n"
            "- Tono: épico, inmersivo, en español con referencias a las cumbres andinas y la forja.\n"
            "- No agregues comillas, ni preámbulos, ni formato markdown.\n"
            "Mensaje:"
        )

        try:
            from core.provider_manager import complete
            messages = [{"role": "user", "content": prompt}]
            raw_content = complete(messages=messages, options={"max_tokens": 60, "temperature": 0.7})
            if raw_content and not raw_content.startswith("[**SYSTEM ERROR"):
                clean = raw_content.strip().replace('"', '').replace('\n', ' ')
                if len(clean) > 150:
                    clean = clean[:147] + "..."
                return {"action": "announce", "message": clean, "type": chosen_type}
        except Exception as e:
            log.warning(f"[GameMaster] Error consultando LLM: {e}. Usando mensaje de reserva.")

        # Fallbacks lore-accurate si el LLM no está disponible
        fallbacks = [
            "Los vientos de la cordillera susurran gloria. ¡La Forja Andina aguarda a los valientes!",
            "El Reino Andino forja leyendas en cada mazmorra. ¡Revisa tu Pase de Batalla con .bp!",
            "Que la llama sagrada guíe vuestras armas en esta jornada, héroes de Azeroth.",
        ]
        return {"action": "announce", "message": random.choice(fallbacks), "type": "fallback_lore"}

    def step_act(self, decision: Dict[str, Any]) -> bool:
        """FASE A: Ejecuta la acción decidida en AzerothCore."""
        act_type = decision.get("action")
        if act_type == "announce":
            msg = decision.get("message", "")
            res = self.tool.execute(action="announce", message=msg, server=self.server_id)
            self._append_audit({
                "action": "announce",
                "message": msg,
                "success": res.success,
                "result": res.stdout or res.stderr,
            })
            return res.success
        return False

    def run_cycle(self) -> Dict[str, Any]:
        """Ejecuta un ciclo completo OODA."""
        self.cycle_count += 1
        log.info(f"[GameMaster] Iniciando ciclo #{self.cycle_count}...")

        obs = self.step_observe()
        decision = self.step_decide(obs)
        success = False

        if decision:
            success = self.step_act(decision)
            log.info(f"[GameMaster] Decisión ejecutada: {decision} (Éxito: {success})")

        report = {
            "cycle": self.cycle_count,
            "observation": obs,
            "decision": decision,
            "success": success,
        }
        self._save_state(report)
        return report

    def start(self) -> None:
        """Inicia el daemon en segundo plano."""
        if self.running:
            return
        self.running = True

        def _loop():
            while self.running:
                try:
                    self.run_cycle()
                except Exception as e:
                    log.error(f"[GameMaster] Excepción en ciclo del daemon: {e}")
                time.sleep(self.interval)

        self._thread = threading.Thread(target=_loop, name="GameMasterDaemon", daemon=True)
        self._thread.start()
        log.info(f"[GameMaster] Daemon iniciado con intervalo de {self.interval}s.")

    def stop(self) -> None:
        """Detiene el daemon."""
        self.running = False
        log.info("[GameMaster] Daemon detenido.")


# ── Singleton facade (module-level API para service_loader y handlers) ────────
_daemon: "GameMasterDaemon | None" = None
_daemon_lock = threading.Lock()


def _get_daemon() -> "GameMasterDaemon":
    global _daemon
    with _daemon_lock:
        if _daemon is None:
            _daemon = GameMasterDaemon()
    return _daemon


def start() -> dict:
    """Arranca el GameMasterDaemon en segundo plano."""
    d = _get_daemon()
    if d.running:
        return {"ok": True, "note": "GameMasterDaemon ya estaba corriendo."}
    d.start()
    return {"ok": True, "note": "GameMasterDaemon iniciado."}


def stop() -> dict:
    """Detiene el GameMasterDaemon."""
    d = _get_daemon()
    d.stop()
    return {"ok": True, "note": "GameMasterDaemon detenido."}


def get_status() -> dict:
    """Retorna el estado del daemon."""
    d = _get_daemon()
    return {
        "running": d.running,
        "cycle_count": d.cycle_count,
        "interval_s": d.interval,
        "server_id": d.server_id,
        "thread_alive": d._thread.is_alive() if d._thread else False,
    }

