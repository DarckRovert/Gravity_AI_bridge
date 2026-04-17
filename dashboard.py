"""
Gravity AI Bridge V9.4 PRO — Dashboard Web Server
Lee web/dashboard.html desde disco en cada request (hot-reload real).
Sirve el HTML actualizado sin necesidad de reiniciar el proceso.
"""
import os

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

    return b"""<!DOCTYPE html><html><head><title>Gravity AI Bridge V10.0</title></head>
    <body style="background:#090c10;color:white;font-family:sans-serif;padding:40px;text-align:center">
    <h2>Gravity AI Bridge V10.0 PRO</h2><p>No se encontro <code>web/dashboard.html</code>.</p>
    <p>Restaura la carpeta web/ del repositorio.</p>
    </body></html>"""

# Compatibilidad con bridge_server.py
DASHBOARD_HTML: bytes = get_dashboard_html()

def _reload_dashboard() -> None:
    """Recarga DASHBOARD_HTML desde disco."""
    global DASHBOARD_HTML
    DASHBOARD_HTML = get_dashboard_html()
