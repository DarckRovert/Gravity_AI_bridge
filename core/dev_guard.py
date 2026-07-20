"""
core/dev_guard.py -- Separacion dura de entorno test/prod (Vocero-pattern).

Uso en bridge_server.py o cualquier mixin:

    from core.dev_guard import dev_only

    @dev_only
    def _serve_my_debug_endpoint(self):
        ...  # Solo accesible si GRAVITY_ENV != "production"

En produccion retorna 404 inmediatamente.
"""

import os
import functools
from typing import Callable


def is_dev_mode() -> bool:
    """
    True si el entorno NO es produccion.
    Activo por defecto en desarrollo; desactivado si GRAVITY_ENV=production.
    """
    return os.environ.get("GRAVITY_ENV", "development").lower() != "production"


def dev_only(handler: Callable) -> Callable:
    """
    Decorador para metodos de handler HTTP.
    Retorna HTTP 404 en produccion sin ejecutar el handler.
    En desarrollo, comportamiento normal.

    Ejemplo:
        @dev_only
        def _serve_dev_echo(self):
            ...
    """
    @functools.wraps(handler)
    def wrapped(self, *args, **kwargs):
        if not is_dev_mode():
            self.send_response(404)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"error": "Not found"}')
            return None
        return handler(self, *args, **kwargs)
    return wrapped
