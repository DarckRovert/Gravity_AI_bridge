import json

from api.routes.mixin_post_chat import PostChatMixin
from api.routes.mixin_post_media import PostMediaMixin
from api.routes.mixin_post_gameserver import PostGameserverMixin
from api.routes.mixin_post_agent import PostAgentMixin
from api.routes.mixin_post_system import PostSystemMixin
from api.routes.mixin_workflow import WorkflowMixin


class PostRoutesMixin(
    PostChatMixin, PostMediaMixin, PostGameserverMixin, PostAgentMixin, PostSystemMixin,
    WorkflowMixin
):
    """
    Master Router para peticiones POST.
    Este archivo ha sido modularizado exitosamente en múltiples submódulos
    para cumplir con la directiva de diseño (Fase 2).
    """

    def do_POST(self):
        if hasattr(self, "_check_rate") and getattr(self, "_check_rate") is not None:
            if not self._check_rate():
                return

        # Enrutado modular secuencial
        if self._handle_post_chat():
            return
        if self._handle_post_media():
            return
        if self._handle_post_gameserver():
            return
        if self._handle_post_agent():
            return
        if self._handle_post_system():
            return
        if self._handle_post_workflow():
            return

        # Fallback si no hay ruta registrada
        self.send_response(404)
        if hasattr(self, "_send_cors") and getattr(self, "_send_cors") is not None:
            self._send_cors()
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({"error": "Endpoint POST no encontrado"}).encode())
