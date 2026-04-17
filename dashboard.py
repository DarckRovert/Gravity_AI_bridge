"""
Gravity AI Bridge V10.0 [Diamond-Tier Edition] — Dashboard Web Server
Lee web/dashboard.html desde disco en cada request (hot-reload real).
Sirve el HTML actualizado sin necesidad de reiniciar el proceso.
"""
import os
import sys

# En modo frozen (PyInstaller exe), __file__ apunta a _MEIPASS (temp).
# Los archivos de datos (web/) están copiados junto al exe por Inno Setup.
# Prioridad: directorio del exe instalado > _MEIPASS > directorio del script.
if getattr(sys, "frozen", False):
    # Directorio real donde está instalado el exe
    BASE_DIR = os.path.dirname(os.path.abspath(sys.executable))
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def get_dashboard_html() -> bytes:
    """Lee el dashboard desde disco en tiempo real (hot-reload)."""
    html_path = os.path.join(BASE_DIR, "web", "dashboard.html")
    if os.path.exists(html_path):
        try:
            with open(html_path, "r", encoding="utf-8") as f:
                return f.read().encode("utf-8")
        except Exception as e:
            print(f"[Dashboard] Error leyendo {html_path}: {e}")

    # Fallback a _MEIPASS si el archivo no está junto al exe
    if getattr(sys, "_MEIPASS", None):
        fallback = os.path.join(sys._MEIPASS, "web", "dashboard.html")
        if os.path.exists(fallback):
            try:
                with open(fallback, "r", encoding="utf-8") as f:
                    return f.read().encode("utf-8")
            except Exception:
                pass

    return b"""<!DOCTYPE html><html><head><title>Gravity AI Bridge V10.0</title></head>
    <body style="background:#090c10;color:white;font-family:sans-serif;padding:40px;text-align:center">
    <h2>Gravity AI Bridge V10.0</h2><p>No se encontro <code>web/dashboard.html</code> en:</p>
    <p><code>""" + html_path.encode() + b"""</code></p>
    <p>Verifica que la carpeta <code>web/</code> exista junto al ejecutable.</p>
    </body></html>"""


# Compatibilidad con bridge_server.py
DASHBOARD_HTML: bytes = get_dashboard_html()


def _reload_dashboard() -> None:
    """Recarga DASHBOARD_HTML desde disco."""
    global DASHBOARD_HTML
    DASHBOARD_HTML = get_dashboard_html()
