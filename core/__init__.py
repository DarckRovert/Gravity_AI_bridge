"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         GRAVITY AI — CORE INITIALIZER V16.0 PRO [Diamond Edition]            ║
║         Punto de entrada unificado para el núcleo de Gravity AI Bridge       ║
╚══════════════════════════════════════════════════════════════════════════════╝

Este módulo consolida y expone las interfaces de bajo nivel, infraestructura,
agentes, herramientas, pipelines de producción y monitores de seguridad del Core.
"""

# ── Infraestructura Base ──────────────────────────────────────────────────────
from . import config_manager  # noqa: F401
from . import data_guardian  # noqa: F401
from . import hardware_profiler  # noqa: F401
from . import key_manager  # noqa: F401
from . import session_manager  # noqa: F401
from . import provider_manager  # noqa: F401
from . import cache_engine  # noqa: F401
from . import cost_tracker  # noqa: F401
from . import audit_log  # noqa: F401
from . import metrics  # noqa: F401
from . import rate_limiter  # noqa: F401

# ── Agentes y Herramientas ────────────────────────────────────────────────────
from . import multi_agent  # noqa: F401
from . import mcp_adapter  # noqa: F401
from . import verification_agent  # noqa: F401
from . import hitl_manager  # noqa: F401
from . import tool_executor  # noqa: F401
from . import turbo_kv  # Optimización KV-cache — conectado a engine_watchdog  # noqa: F401

# ── Pipeline de Producción e Integraciones de Alta Gama ─────────────────────────
from . import security_monitor  # noqa: F401
from . import image_queue  # noqa: F401
from . import video_pipeline  # noqa: F401
from . import deploy_manager  # noqa: F401
from . import game_server_manager  # noqa: F401
from . import ai_process_manager  # noqa: F401
from . import animation_engine  # noqa: F401
from . import gravity_brain  # noqa: F401
from . import engine_watchdog  # noqa: F401
