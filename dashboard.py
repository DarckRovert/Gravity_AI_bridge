"""
╔══════════════════════════════════════════════════════════════╗
║     GRAVITY AI BRIDGE V9.1 PRO [Diamond-Tier Edition] — DASHBOARD WEB CON CHAT          ║
║     SPA interactiva: Estado + Chat + Gestión de modelos       ║
╚══════════════════════════════════════════════════════════════╝
Servidor Flask-less: HTTP puro para cero dependencias extra.
Sirve dashboard.html en / con chat streaming via /v1/chat/stream
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
    """Reads the premium Vue-like SPA from disk. Fallback to basic HTML if missing."""
    html_path = os.path.join(BASE_DIR, "web", "dashboard.html")
    if os.path.exists(html_path):
        try:
            with open(html_path, "r", encoding="utf-8") as f:
                return f.read().encode("utf-8")
        except Exception as e:
            print(f"[Dashboard] Error reading web/dashboard.html: {e}")
    
    # Fallback minimalista por si se borra la carpeta web/
    return b"""<!DOCTYPE html><html><head><title>Gravity AI Error</title></head>
    <body style="background:#090c10;color:white;font-family:sans-serif;padding:40px;text-align:center">
    <h2>Error de Interfaz V9.1 PRO</h2><p>No se encontro <code>web/dashboard.html</code>.</p>
    <p>Por favor ejecuta nuevamente el instalador o restaura la carpeta web/.</p>
    </body></html>"""

class DashboardHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/" or self.path == "/dashboard":
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

    def log_message(self, fmt, *args): pass


def run(port: int = 7862):
    server = ThreadingHTTPServer(("0.0.0.0", port), DashboardHandler)
    print(f"[Gravity Dashboard] http://localhost:{port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()


if __name__ == "__main__":
    run()
