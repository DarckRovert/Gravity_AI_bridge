"""
Gravity AI Bridge V9.3.1 PRO — Dashboard Web Server
SPA interactiva: Estado + Chat + Vision Studio + Gestion de modelos
Servidor HTTP puro — cero dependencias extra.
Sirve web/dashboard.html en / con CORS habilitado.
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
    """Lee el SPA premium desde disco. Fallback a HTML de error si no existe."""
    html_path = os.path.join(BASE_DIR, "web", "dashboard.html")
    if os.path.exists(html_path):
        try:
            with open(html_path, "r", encoding="utf-8") as f:
                return f.read().encode("utf-8")
        except Exception as e:
            print(f"[Dashboard] Error leyendo web/dashboard.html: {e}")

    # Fallback: HTML minimalista si se borra la carpeta web/
    return b"""<!DOCTYPE html><html><head><title>Gravity AI Bridge V9.3</title></head>
    <body style="background:#090c10;color:white;font-family:sans-serif;padding:40px;text-align:center">
    <h2>Gravity AI Bridge V9.3 PRO</h2><p>No se encontro <code>web/dashboard.html</code>.</p>
    <p>Restaura la carpeta web/ del repositorio.</p>
    </body></html>"""


# Constante de modulo — importable directamente desde bridge_server.py
# Se evalua en el primer import (lazy-load real en disco)
DASHBOARD_HTML: bytes = get_dashboard_html()


def _reload_dashboard() -> None:
    """Recarga la constante DASHBOARD_HTML desde disco sin reiniciar el proceso."""
    global DASHBOARD_HTML
    DASHBOARD_HTML = get_dashboard_html()


class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path in ("/", "/dashboard"):
            body = DASHBOARD_HTML
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
