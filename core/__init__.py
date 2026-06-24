"""
╔══════════════════════════════════════════════════════════════════════════════╗
║         GRAVITY AI — CORE INITIALIZER V16.0 PRO [Diamond Edition]            ║
║         Punto de entrada unificado para el núcleo de Gravity AI Bridge       ║
╚══════════════════════════════════════════════════════════════════════════════╝

Este módulo consolida y expone las interfaces de bajo nivel, infraestructura,
agentes, herramientas, pipelines de producción y monitores de seguridad del Core.
"""

# ── Infraestructura Base ──────────────────────────────────────────────────────
from . import config_manager
from . import data_guardian
from . import hardware_profiler
from . import key_manager
from . import session_manager
from . import provider_manager
from . import cache_engine
from . import cost_tracker
from . import audit_log
from . import metrics
from . import rate_limiter

# ── Agentes y Herramientas ────────────────────────────────────────────────────
from . import multi_agent
from . import mcp_adapter
from . import verification_agent
from . import hitl_manager
from . import tool_executor
from . import turbo_kv  # Optimización KV-cache — conectado a engine_watchdog

# ── Pipeline de Producción e Integraciones de Alta Gama ─────────────────────────
from . import security_monitor
from . import image_queue
from . import video_pipeline
from . import deploy_manager
from . import game_server_manager
from . import ai_process_manager
from . import animation_engine
from . import gravity_brain
from . import engine_watchdog
