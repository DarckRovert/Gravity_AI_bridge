"""
Módulo J.A.R.V.I.S: HUD Espacial (Pilar 5)
Capa de visualización 2D/3D superpuesta sobre Windows (Click-through).
Utiliza PySide6 (Qt) acelerado por hardware para efectos visuales sin consumir CPU.
"""

import sys
import threading
import time
from core.logger import log

try:
    from PySide6.QtCore import Qt, QTimer, QPoint
    from PySide6.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout
    from PySide6.QtGui import QColor, QPalette, QFont
    PYSIDE_AVAILABLE = True
except ImportError:
    PYSIDE_AVAILABLE = False
    log.warning("[JARVIS-HUD] PySide6 no detectado. El HUD Espacial está desactivado.")
    print("\n" + "="*50)
    print(" HUD ESPACIAL DESACTIVADO (FALTA LIBRERIA)")
    print(" Para activar el HUD holográfico transparente,")
    print(" instala las dependencias gráficas de Qt:")
    print(" -> pip install PySide6")
    print("="*50 + "\n")

class SpatialHUD(QWidget if PYSIDE_AVAILABLE else object):
    def __init__(self):
        if not PYSIDE_AVAILABLE:
            return
            
        super().__init__()
        # Configurar ventana: Sin bordes, siempre arriba, transparente y click-through
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Ubicación y tamaño inicial (Arriba a la derecha)
        self.setGeometry(100, 100, 400, 200)

        # Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(10, 10, 10, 10)

        # Label principal con estilo "Holograma Stark"
        self.text_label = QLabel("GRAVITY V16.7\nSISTEMAS EN LÍNEA")
        self.text_label.setStyleSheet("""
            QLabel {
                color: #00F0FF;
                font-family: 'Consolas';
                font-size: 16px;
                font-weight: bold;
                background-color: rgba(0, 20, 40, 120);
                border: 1px solid #00F0FF;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        self.text_label.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        self.layout.addWidget(self.text_label)

        self.move_to_top_right()

    def move_to_top_right(self):
        if not PYSIDE_AVAILABLE: return
        screen = QApplication.primaryScreen().geometry()
        x = screen.width() - self.width() - 20
        y = 40
        self.move(x, y)

    def update_text(self, text: str):
        if not PYSIDE_AVAILABLE: return
        self.text_label.setText(text)
        self.text_label.adjustSize()
        self.adjustSize()
        self.move_to_top_right()

def _run_hud():
    if not PYSIDE_AVAILABLE:
        return
        
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
        
    hud = SpatialHUD()
    hud.show()
    
    # Simular actualizaciones de telemetría desde el Sensory Bus
    def simulate_telemetry():
        import random
        cpu = random.randint(30, 80)
        hud.update_text(f"GRAVITY V16.7\nSISTEMAS EN LÍNEA\nAPU LOAD: {cpu}%")
        
    timer = QTimer()
    timer.timeout.connect(simulate_telemetry)
    timer.start(2000)

    app.exec()

def start_hud_daemon():
    """Lanza el HUD Espacial en un hilo separado para no bloquear."""
    t = threading.Thread(target=_run_hud, daemon=True, name="SpatialHUD")
    t.start()
    return t

if __name__ == "__main__":
    start_hud_daemon()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
