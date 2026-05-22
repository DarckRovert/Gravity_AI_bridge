"""
╔══════════════════════════════════════════════════════════════════════════════╗
║               GRAVITY OBS CLIENT WRAPPER — core/obs_client.py                ║
║        Backwards-compatible bridge pointing to integrations.obs.client       ║
╚══════════════════════════════════════════════════════════════════════════════╗
This file serves as a backwards-compatibility wrapper to prevent breaking imports 
in mixins, legacy modules, and third-party systems that expect core.obs_client.
All active logic has been decoupled and resides in integrations/obs/client.py.
"""

from integrations.obs.client import (
    OBSClient,
    get_client,
    auto_connect_if_configured,
    OBS_AVAILABLE
)

# Re-export key objects for legacy callers
__all__ = [
    "OBSClient",
    "get_client",
    "auto_connect_if_configured",
    "OBS_AVAILABLE"
]
