"""
Gravity AI Bridge V9.4 PRO — Dashboard Web Server
Lee web/dashboard.html desde disco en cada request (hot-reload real).
Sirve el HTML actualizado sin necesidad de reiniciar el proceso.
"""
import json
import os
import sys
import time
import uuid
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import urllib.parse

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_dashboard_html() -> bytes:
    """Lee el dashboard desde disco en tiempo real (hot-reload)."""
    html_path = os.path.join(BASE_DIR, "web", "dashboard.html")
    if os.path.exists(html_path):
        try:
            with open(html_path, "r", encoding="utf-8") as f:
                return f.read().encode("utf-8")
        except Exception as e:
            print(f"[Dashboard] Error leyendo web/dashboard.html: {e}")

    return b"""<!DOCTYPE html><html><head><title>Gravity AI Bridge V9.4</title></head>
    <body style="background:#090c10;color:white;font-family:sans-serif;padding:40px;text-align:center">
    <h2>Gravity AI Bridge V9.4 PRO</h2><p>No se encontro <code>web/dashboard.html</code>.</p>
    <p>Restaura la carpeta web/ del repositorio.</p>
    </body></html>"""


# Compatibilidad con bridge_server.py que importa DASHBOARD_HTML como bytes.
# Ahora es una propiedad lazy: siempre lee del disco en el momento del import.
# Para hot-reload real, usar get_dashboard_html() directamente.
DASHBOARD_HTML: bytes = get_dashboard_html()


def _reload_dashboard() -> None:
    """Recarga DASHBOARD_HTML desde disco (llamar tras editar web/dashboard.html sin reiniciar)."""
    global DASHBOARD_HTML
    DASHBOARD_HTML = get_dashboard_html()


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/dashboard"):
            # Lectura dinámica en cada request = hot-reload automático
            body = get_dashboard_html()
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self.send_response(301)
            self.send_header("Location", "/")
            self.end_headers()

    def log_message(self, fmt, *args):
        pass  # Silenciar logs del servidor secundario


def run(port: int = 7862):
    server = ThreadingHTTPServer(("0.0.0.0", port), DashboardHandler)
    print(f"[Gravity Dashboard] http://localhost:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    run()
