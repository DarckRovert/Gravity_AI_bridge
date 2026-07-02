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
        if self.is_running():
            log.info("FastFlowLM ya está corriendo (detectado por puerto o proceso).")
            return True
            
        env = os.environ.copy()
        
        # En arquitecturas de driver actualizadas (32.0+), FastFlowLM detecta XRT de manera autónoma.
        # Forzar XLNX_VART_FIRMWARE hacia un .dll estático obsoleto provoca un crash instantáneo (Exit Code 1).
        
        # Desactivar la verificación de actualización
        env["FLM_DISABLE_UPDATE_CHECK"] = "1"
        
        # Inyectar el entorno conda ryzen-ai-1.3.1 (VitisAIExecutionProvider) en el PATH.
        # FastFlowLM necesita este entorno para comunicarse con la NPU Phoenix (XDNA).
        _ryzen_env = r"C:\Users\darck\miniconda3\envs\ryzen-ai-1.3.1"
        _ryzen_scripts = os.path.join(_ryzen_env, "Scripts")
        if os.path.isdir(_ryzen_env):
            env["PATH"] = _ryzen_env + os.pathsep + _ryzen_scripts + os.pathsep + env.get("PATH", "")
            env["CONDA_PREFIX"] = _ryzen_env
            env["CONDA_DEFAULT_ENV"] = "ryzen-ai-1.3.1"
            log.info(f"Entorno Ryzen AI 1.3.1 inyectado: {_ryzen_env}")
        else:
            log.warning("Entorno ryzen-ai-1.3.1 no encontrado. La NPU puede usar CPU como fallback.")
        
        try:
            log.info(f"Levantando NPU (FastFlowLM) con modelo {self._model} en puerto {self._port}...")
            # Usamos creationflags=subprocess.CREATE_NEW_PROCESS_GROUP para aislarlo de la consola de Gravity
            self._process = subprocess.Popen(
                ["flm", "serve", self._model, "--port", str(self._port)],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
            )
            self._running = True
            time.sleep(2)  # Darle tiempo para arrancar
            return self.is_running()
        except FileNotFoundError:
            log.error("El ejecutable 'flm' no se encuentra en el PATH.")
            return False
        except Exception as e:
            log.error(f"Error al iniciar FastFlowLM: {e}")
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
