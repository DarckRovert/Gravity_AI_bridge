import time
import psutil
import threading
from collections import deque
from core.logger import log

class ResourceWatchdog:
    """
    OODA Loop Background Watchdog (Observe, Orient, Decide, Act).
    Monitorea los recursos del sistema y mata procesos de IA "stray" (ComfyUI, LM Studio, etc.) 
    si se detecta inactividad, evitando memory leaks en la Radeon 780M / RAM.
    """
    def __init__(self):
        self.running = False
        self._thread = None
        self.idle_timeout_seconds = 1800  # 30 minutos de gracia
        self._last_active_time = time.time()
        self.ram_threshold_percent = 75.0
        self.swap_threshold_percent = 90.0
        self.target_keywords = ["comfyui", "fooocus", "gradio"]
        self.protected_keywords = ["lm studio", "ollama"]
        self.history = deque(maxlen=20)
        
    def _is_gravity_active(self):
        try:
            from core.video.pipeline import get_queue_status
            status = get_queue_status()
            if status.get("current_job") is not None:
                return True
        except Exception:
            pass
            
        try:
            from core.workflow_engine import list_jobs
            for job in list_jobs():
                if job.get("status") == "running":
                    return True
        except Exception:
            pass

        return False

    def _kill_stray_ai_processes(self) -> int:
        """Busca y mata procesos pesados de IA de generación de imágenes."""
        log.info("[ResourceWatchdog] OODA: Decisión tomada -> Matar procesos de IA inactivos para liberar RAM/VRAM.")
        killed = 0
        killed_list = []
        target_keywords = self.target_keywords
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline') or []
                name = (proc.info.get('name') or "").lower()
                cmd_str = " ".join(cmdline).lower()
                
                # Check for matching keywords
                is_target = any(kw in name or kw in cmd_str for kw in target_keywords)
                
                if is_target:
                    # Ignore the watchdog itself or main gravity processes
                    if "engine_watchdog.py" not in cmd_str and "resource_watchdog.py" not in cmd_str and "gravity_daemon" not in cmd_str:
                        proc.kill()
                        killed += 1
                        killed_list.append(name or f"PID {proc.pid}")
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        if killed > 0:
            log.info(f"[ResourceWatchdog] OODA: Acción ejecutada -> {killed} procesos de IA terminados con éxito: {killed_list}")
            self.history.append({
                "timestamp": timestamp,
                "action": "Cleanup",
                "details": f"Terminados {killed} procesos: {', '.join(killed_list)}"
            })
        else:
            log.info("[ResourceWatchdog] Escaneo completado sin procesos eliminados.")
            self.history.append({
                "timestamp": timestamp,
                "action": "Scan",
                "details": "Escaneo ejecutado. Sin procesos huérfanos activos."
            })
        return killed

    def notify_activity(self):
        """Notifica actividad al watchdog (ej. cuando el usuario chatea)."""
        self._last_active_time = time.time()

    def get_status(self) -> dict:
        """Devuelve un estado serializable del Resource Watchdog."""
        now = time.time()
        try:
            mem = psutil.virtual_memory().percent
            swap = psutil.swap_memory().percent
        except Exception:
            mem = 0.0
            swap = 0.0
            
        return {
            "running": self.running,
            "idle_timeout_seconds": self.idle_timeout_seconds,
            "idle_duration": int(now - self._last_active_time),
            "ram_threshold": self.ram_threshold_percent,
            "swap_threshold": self.swap_threshold_percent,
            "current_ram": mem,
            "current_swap": swap,
            "target_keywords": self.target_keywords,
            "protected_keywords": self.protected_keywords,
            "history": list(self.history)
        }

    def trigger_cleanup(self) -> int:
        """Ejecuta una limpieza forzada manual."""
        return self._kill_stray_ai_processes()

    def _loop(self):
        log.info("[ResourceWatchdog] OODA Loop iniciado. Vigilando el estado de la RAM/VRAM.")
        while self.running:
            time.sleep(10)
            
            # Observe & Orient
            is_active = self._is_gravity_active()
            if is_active:
                self._last_active_time = time.time()
            
            # Decide & Act
            idle_duration = time.time() - self._last_active_time
            if not is_active and idle_duration > self.idle_timeout_seconds:
                # El sistema ha estado inactivo más allá del timeout
                try:
                    mem = psutil.virtual_memory()
                    swap = psutil.swap_memory()
                    if mem.percent > self.ram_threshold_percent or swap.percent > self.swap_threshold_percent:
                        log.warning(f"[ResourceWatchdog] Limpieza autónoma activada (RAM: {mem.percent}%, Swap: {swap.percent}%). Sistema inactivo por {int(idle_duration)}s.")
                        self._kill_stray_ai_processes()
                        # Reset timeout so we don't spam kills
                        self._last_active_time = time.time() 
                except Exception as e:
                    log.error(f"[ResourceWatchdog] Error evaluando memoria: {e}")

    def start(self):
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self._loop, daemon=True, name="GravityResourceWatchdog")
            self._thread.start()

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=2)

resource_watchdog = ResourceWatchdog()
