"""
╔══════════════════════════════════════════════════════════════════════════════╗
║             GRAVITY OBS INTEGRATION — integrations/obs/__init__.py           ║
║              Plugin definition implementing GravityIntegration               ║
╚══════════════════════════════════════════════════════════════════════════════╗
"""

from core.base_plugin import GravityIntegration
from .client import get_client, auto_connect_if_configured


class OBSIntegration(GravityIntegration):

    @property
    def name(self) -> str:
        return "obs"

    @property
    def description(self) -> str:
        return "Control dinámico de escenas, audios, streams y overlays en OBS Studio por WebSockets"

    def initialize(self) -> bool:
        auto_connect_if_configured()
        return True

    def shutdown(self) -> bool:
        client = get_client()
        client.disconnect()
        return True

    def get_status(self) -> dict:
        client = get_client()
        return client.get_status()
