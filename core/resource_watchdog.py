import time
import psutil
import threading
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
        self.idle_timeout_seconds = 600  # 10 minutos de gracia
        self._last_active_time = time.time()
        
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

    def _kill_stray_ai_processes(self):
        """Busca y mata procesos pesados de IA (Python corriendo ComfyUI, Ollama, LM Studio)."""
        log.info("[ResourceWatchdog] OODA: Decisión tomada -> Matar procesos de IA inactivos para liberar RAM/VRAM.")
        killed = 0
        target_keywords = ["comfyui", "lm studio", "ollama", "fooocus", "gradio"]
        
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
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
        if killed > 0:
            log.info(f"[ResourceWatchdog] OODA: Acción ejecutada -> {killed} procesos de IA terminados con éxito.")

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
                # Chequeamos si la RAM está alta (>70%)
                try:
                    mem = psutil.virtual_memory()
                    swap = psutil.swap_memory()
                    # Limpieza de rutina: Si la RAM física pasa del 75% tras 10 min de inactividad, limpiamos para ahorrar recursos.
                    # Limpieza crítica: Si el Swap pasa del 90%, limpiamos por emergencia.
                    if mem.percent > 75.0 or swap.percent > 90.0:
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
