import os
import subprocess
import time
import logging
import psutil

log = logging.getLogger("npu_manager")

class NPUManager:
    """Gestiona el ciclo de vida del proceso FastFlowLM (flm serve)."""
    
    def __init__(self):
        self._process = None
        self._running = False
        self._port = 52625
        self._model = "llama3.2:1b"
        
    def is_running(self) -> bool:
        # 1. Chequeo por proceso lanzado internamente
        if self._process is not None and self._process.poll() is None:
            return True
            
        # 2. Chequeo global por nombre de proceso flm.exe
        try:
            import psutil
            for proc in psutil.process_iter(['name']):
                if proc.info['name'] and proc.info['name'].lower() == 'flm.exe':
                    return True
        except:
            pass
            
        # 3. Chequeo por puerto (por si el BAT u otro proceso lo arrancó)
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(0.5)
                if s.connect_ex(('127.0.0.1', self._port)) == 0:
                    return True
        except:
            pass
            
        return False

    def start(self) -> bool:
        log.warning("FastFlowLM deshabilitado: hardware Ryzen 7 8700G posee NPU XDNA1 (FastFlowLM requiere NPU XDNA2).")
        log.info("Usa LM Studio con aceleración Vulkan para tu iGPU Radeon 780M (Plan B) para correr el LLM local.")
        return False

    def stop(self) -> bool:
        if not self.is_running():
            return True
            
        log.info("Deteniendo NPU (FastFlowLM)...")
        try:
            parent = psutil.Process(self._process.pid)
            for child in parent.children(recursive=True):
                child.kill()
            parent.kill()
        except Exception as e:
            log.error(f"Error al matar proceso NPU: {e}")
            
        self._process = None
        self._running = False
        return True

npu_manager = NPUManager()
