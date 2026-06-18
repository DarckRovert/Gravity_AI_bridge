"""
╔══════════════════════════════════════════════════════════════════════════════╗
║          GRAVITY AI - COST TRACKER V16.0 PRO [Diamond-Tier Edition]           ║
║                   Tracking de costes cloud en tiempo real                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import json
import os
import time
import threading
from datetime import date
from typing import Dict, Tuple, Any, Optional

# Subimos un nivel para que la base sea la raíz de F:\Gravity_AI_bridge
BASE_DIR        = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COST_LOG_FILE   = os.path.join(BASE_DIR, "_cost_log.json")
SETTINGS_FILE   = os.path.join(BASE_DIR, "_settings.json")

_lock           = threading.RLock()
_session_cost   : float = 0.0
_session_tokens : Dict[str, int] = {"input": 0, "output": 0}


def _load_log() -> Dict[str, Any]:
    with _lock:
        try:
            if not os.path.exists(COST_LOG_FILE):
                return {}
            with open(COST_LOG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except Exception:
            return {}


def _save_log(log: Dict[str, Any]) -> None:
    with _lock:
        try:
            with open(COST_LOG_FILE, "w", encoding="utf-8") as f:
                json.dump(log, f, indent=2, ensure_ascii=False)
        except Exception:
            pass


def _get_daily_limit() -> float:
    with _lock:
        try:
            if not os.path.exists(SETTINGS_FILE):
                return 10.0
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
        with _lock:
            return _session_cost

    @staticmethod
    def get_session_tokens() -> Dict[str, int]:
        with _lock:
            return dict(_session_tokens)

    @staticmethod
    def get_daily_cost(day: Optional[str] = None) -> float:
        today = day or str(date.today())
        with _lock:
            log = _load_log()
            day_data = log.get(today, {})
            if not isinstance(day_data, dict):
                return 0.0
            return sum(float(v.get("total_cost", 0.0)) for v in day_data.values() if isinstance(v, dict))

    @staticmethod
    def get_daily_breakdown(day: Optional[str] = None) -> Dict[str, Any]:
        today = day or str(date.today())
        with _lock:
            log = _load_log()
            bd = log.get(today, {})
            return dict(bd) if isinstance(bd, dict) else {}

    @staticmethod
    def check_limit() -> Tuple[bool, float]:
        """Returns (over_limit, daily_cost)."""
        with _lock:
            daily  = CostTracker.get_daily_cost()
            limit  = _get_daily_limit()
            return daily >= limit, daily

    @staticmethod
    def set_daily_limit(usd: float) -> None:
        with _lock:
            try:
                s = {}
                if os.path.exists(SETTINGS_FILE):
                    with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                        s = json.load(f)
                        if not isinstance(s, dict):
                            s = {}
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
        with _lock:
            session = _session_cost
            daily   = CostTracker.get_daily_cost()
            limit   = _get_daily_limit()
            bd      = CostTracker.get_daily_breakdown()

            lines   = [f"💰 Sesión: ${session:.4f} | Día: ${daily:.4f} / ${limit:.2f}"]
            if bd:
                lines.append("")
                for prov, data in bd.items():
                    if isinstance(data, dict):
                        lines.append(
                            f"  {prov:<18} ${data.get('total_cost', 0.0):.4f} "
                            f"({data.get('calls', 0)} llamadas | "
                            f"{data.get('input_tokens', 0):,}↓ {data.get('output_tokens', 0):,}↑ tokens)"
                        )
            return "\n".join(lines)

