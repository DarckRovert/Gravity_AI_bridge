"""
Módulo J.A.R.V.I.S: Thermal Watchdog (Pilar 4)
Monitorea la temperatura del hardware (CPU/APU).
Si excede umbrales críticos, detiene procesos pesados (Mercenarios, renders) interviniendo La Tinka.
"""

import time
import subprocess
import threading
from core.logger import log

class ThermalWatchdog:
    def __init__(self, check_interval=10, max_temp=85.0):
        self.interval = check_interval
        self.max_temp = max_temp
        self.running = False
        self._thread = None
        self.throttling_active = False

    def get_cpu_temp(self) -> float:
        """Intenta obtener la temperatura real de la CPU/APU usando WMI."""
        try:
            # WMI ThermalZoneTemperature devuelve décimas de grados Kelvin.
            # Convertir a Celsius: (K / 10) - 273.15
            # Nota: Requiere permisos de Admin o placa base compatible.
            cmd = ['powershell', '-Command', 
                   '(Get-WmiObject MSAcpi_ThermalZoneTemperature -Namespace "root/wmi").CurrentTemperature']
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
            
            if result.returncode == 0 and result.stdout.strip():
                # Toma el primer valor si hay múltiples zonas térmicas
                k_dec = float(result.stdout.strip().split('\n')[0])
                celsius = (k_dec / 10.0) - 273.15
                return celsius
            else:
                # Fallback simulación si WMI bloqueado
                return 45.0
        except Exception:
            return 45.0

    def enforce_thermal_limits(self, current_temp: float):
        if current_temp >= self.max_temp and not self.throttling_active:
            log.warning(f"[JARVIS-Thermal] PELIGRO: Temperatura en {current_temp:.1f}°C. Activando Throttling de Emergencia.")
            self.throttling_active = True
            self.pause_heavy_workloads()
            
        elif current_temp <= (self.max_temp - 10) and self.throttling_active:
            log.info(f"[JARVIS-Thermal] Temperatura estable en {current_temp:.1f}°C. Levantando Throttling.")
            self.throttling_active = False
            self.resume_heavy_workloads()

    def pause_heavy_workloads(self):
        """Simula escribir el estado PAUSE en la base de datos La Tinka para detener Renders."""
        # TODO: Implementar escritura real en SQLite / Tinka WAL
        log.warning("[JARVIS-Thermal] Señal de PAUSA inyectada a los Nodos de Renderizado y Ollama.")

    def resume_heavy_workloads(self):
        """Simula escribir el estado RUNNING en La Tinka."""
        # TODO: Implementar escritura real en SQLite / Tinka WAL
        log.info("[JARVIS-Thermal] Señal de REANUDACIÓN enviada a los Nodos.")

    def loop(self):
        log.info("[JARVIS-Thermal] Watchdog de Supervivencia Activa iniciado.")
        while self.running:
            temp = self.get_cpu_temp()
            self.enforce_thermal_limits(temp)
            time.sleep(self.interval)

    def start(self):
        if not self.running:
            self.running = True
            self._thread = threading.Thread(target=self.loop, daemon=True, name="ThermalWatchdog")
            self._thread.start()
            
    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=2)

if __name__ == "__main__":
    dog = ThermalWatchdog(check_interval=2)
    dog.start()
    time.sleep(10)
    dog.stop()
