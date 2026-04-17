"""
╔══════════════════════════════════════════════════════════════╗
║     GRAVITY AI BRIDGE V10.0 — System Tray Manager           ║
║     Icono de bandeja del sistema + menú contextual           ║
╚══════════════════════════════════════════════════════════════╝

Requiere: pip install pystray Pillow
"""

import threading
import webbrowser
import time
import os
import sys

DASHBOARD_URL = "http://127.0.0.1:7860"
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
ICON_PATH     = os.path.join(BASE_DIR, "assets", "gravity_icon.ico")

# ── Colores del icono dinámico cuando no hay .ico ─────────────────────────────
_ACCENT  = (79,  70,  229)   # Quantum Violet
_BG      = (9,   12,  16 )   # Deep Space


def _build_icon_image(size: int = 64, pulsing: bool = False) -> "PIL.Image.Image":
    """Genera el icono de bandeja en memoria si no existe el .ico."""
    from PIL import Image, ImageDraw
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    cx, cy, r = size // 2, size // 2, size // 2 - 2
    # Fondo oscuro circular
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(*_BG, 255))
    # Anillo Quantum Violet
    ring_w = max(2, size // 12)
    draw.ellipse(
        [cx - r + ring_w, cy - r + ring_w, cx + r - ring_w, cy + r - ring_w],
        outline=(*_ACCENT, 230 if not pulsing else 160),
        width=ring_w
    )
    # Letra "G" central
    from PIL import ImageFont
    try:
        font = ImageFont.truetype("arial.ttf", size // 3)
    except Exception:
        font = ImageFont.load_default()
    text = "G"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((cx - tw // 2, cy - th // 2), text, fill=(*_ACCENT, 255), font=font)
    return img


def _load_icon():
    """Carga el .ico o genera el ícono dinámicamente."""
    try:
        from PIL import Image
        if os.path.exists(ICON_PATH):
            return Image.open(ICON_PATH)
        return _build_icon_image(64)
    except ImportError:
        raise SystemExit("[GravityTray] Pillow no instalado. Ejecuta: pip install Pillow")


# ── Bridge Status ──────────────────────────────────────────────────────────────

def _bridge_online() -> bool:
    try:
        import urllib.request
        urllib.request.urlopen(f"{DASHBOARD_URL}/health", timeout=1)
        return True
    except Exception:
        return False


# ── Tray Actions ──────────────────────────────────────────────────────────────

def _open_dashboard(icon, item):
    webbrowser.open(DASHBOARD_URL)


def _quit(icon, item):
    icon.stop()
    # Señalizar al launcher que termine también
    _stop_event.set()


_stop_event = threading.Event()


def _status_text() -> str:
    return "● Bridge Online" if _bridge_online() else "○ Bridge Offline"


def _build_menu(pystray):
    return pystray.Menu(
        pystray.MenuItem("Gravity AI Bridge V10.0", None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("🌐 Abrir Dashboard", _open_dashboard, default=True),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(_status_text, None, enabled=False),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("✕ Salir", _quit),
    )


# ── Pulsing icon thread ────────────────────────────────────────────────────────

def _pulse_loop(icon):
    """Hace pulsar el icono durante el arranque hasta que el bridge responda."""
    pulsing = True
    timeout = 90
    t0 = time.time()
    while not _bridge_online() and time.time() - t0 < timeout:
        icon.icon = _build_icon_image(64, pulsing=pulsing)
        pulsing = not pulsing
        time.sleep(0.8)
    # Icono estático una vez online
    icon.icon = _load_icon()
    icon.title = "Gravity AI Bridge V10.0 — Online"


# ── Entry Point ───────────────────────────────────────────────────────────────

def run_tray():
    """Inicia el icono de bandeja del sistema. Bloqueante."""
    try:
        import pystray
    except ImportError:
        raise SystemExit("[GravityTray] pystray no instalado. Ejecuta: pip install pystray")

    img  = _build_icon_image(64, pulsing=True)  # Inicia pulsante
    menu = _build_menu(pystray)

    icon = pystray.Icon(
        name    = "GravityAIBridge",
        icon    = img,
        title   = "Gravity AI Bridge V10.0 — Iniciando...",
        menu    = menu,
    )

    # Hilo de pulso durante arranque
    threading.Thread(target=_pulse_loop, args=(icon,), daemon=True).start()

    icon.run()


if __name__ == "__main__":
    run_tray()
