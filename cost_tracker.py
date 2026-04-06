"""
╔══════════════════════════════════════════════════════════════╗
║     GRAVITY AI — COST TRACKER V7.1                           ║
║     Tracking de costes cloud en tiempo real                  ║
╚══════════════════════════════════════════════════════════════╝
Registra tokens consumidos y coste estimado por proveedor.
Persistencia en _cost_log.json. Límites diarios configurables.
"""

import json
import os
import time
import threading
from datetime import date

BASE_DIR        = os.path.dirname(os.path.abspath(__file__))
COST_LOG_FILE   = os.path.join(BASE_DIR, "_cost_log.json")
SETTINGS_FILE   = os.path.join(BASE_DIR, "_settings.json")

_lock           = threading.Lock()
_session_cost   = 0.0
_session_tokens = {"input": 0, "output": 0}


def _load_log() -> dict:
    try:
        with open(COST_LOG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _save_log(log: dict) -> None:
    try:
        with open(COST_LOG_FILE, "w", encoding="utf-8") as f:
            json.dump(log, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def _get_daily_limit() -> float:
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return float(json.load(f).get("cost_limit_usd", 10.0))
    except Exception:
        return 10.0


class CostTracker:
    """
    Tracks token usage and estimated USD cost per provider and model.
    Only cloud providers incur cost — local providers return 0.0.
    """

    @staticmethod
    def record(
        provider:      str,
        model:         str,
        input_tokens:  int,
        output_tokens: int,
        cost_usd:      float = 0.0,
    ) -> None:
        global _session_cost, _session_tokens
        today = str(date.today())

        with _lock:
            _session_cost          += cost_usd
            _session_tokens["input"]  += input_tokens
            _session_tokens["output"] += output_tokens

            log = _load_log()
            if today not in log:
                log[today] = {}
            if provider not in log[today]:
                log[today][provider] = {"total_cost": 0.0, "input_tokens": 0, "output_tokens": 0, "calls": 0}

            log[today][provider]["total_cost"]    += cost_usd
            log[today][provider]["input_tokens"]  += input_tokens
            log[today][provider]["output_tokens"] += output_tokens
            log[today][provider]["calls"]         += 1
            _save_log(log)

    @staticmethod
    def get_session_cost() -> float:
        return _session_cost

    @staticmethod
    def get_session_tokens() -> dict:
        return dict(_session_tokens)

    @staticmethod
    def get_daily_cost(day: str | None = None) -> float:
        today = day or str(date.today())
        log   = _load_log()
        return sum(v.get("total_cost", 0.0) for v in log.get(today, {}).values())

    @staticmethod
    def get_daily_breakdown(day: str | None = None) -> dict:
        today = day or str(date.today())
        return _load_log().get(today, {})

    @staticmethod
    def check_limit() -> tuple[bool, float]:
        """Returns (over_limit, daily_cost)."""
        daily  = CostTracker.get_daily_cost()
        limit  = _get_daily_limit()
        return daily >= limit, daily

    @staticmethod
    def set_daily_limit(usd: float) -> None:
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                s = json.load(f)
            s["cost_limit_usd"] = usd
            with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
                json.dump(s, f, indent=4, ensure_ascii=False)
        except Exception:
            pass

    @staticmethod
    def estimate(
        provider_name: str,
        model:         str,
        input_chars:   int,
        output_chars:  int = 500,
    ) -> float:
        """Estimates cost in USD without recording it."""
        try:
            from providers.registry import ProviderRegistry
            plugin = next(
                (p for p in ProviderRegistry.get_all_plugins() if p.name == provider_name),
                None
            )
            if not plugin:
                return 0.0
            costs  = plugin.get_cost_per_million_tokens(model)
            inp_t  = input_chars  / 4.0
            out_t  = output_chars / 4.0
            return (inp_t * costs["input"] + out_t * costs["output"]) / 1_000_000
        except Exception:
            return 0.0

    @staticmethod
    def reset_session() -> None:
        global _session_cost, _session_tokens
        with _lock:
            _session_cost = 0.0
            _session_tokens = {"input": 0, "output": 0}

    @staticmethod
    def summary_text() -> str:
        """Returns a formatted summary string for display."""
        session = _session_cost
        daily   = CostTracker.get_daily_cost()
        limit   = _get_daily_limit()
        bd      = CostTracker.get_daily_breakdown()

        lines   = [f"💰 Sesión: ${session:.4f} | Día: ${daily:.4f} / ${limit:.2f}"]
        if bd:
            lines.append("")
            for prov, data in bd.items():
                lines.append(
                    f"  {prov:<18} ${data['total_cost']:.4f} "
                    f"({data['calls']} llamadas | "
                    f"{data['input_tokens']:,}↓ {data['output_tokens']:,}↑ tokens)"
                )
        return "\n".join(lines)
