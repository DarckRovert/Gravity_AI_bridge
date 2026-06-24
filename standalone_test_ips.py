import sys
import os
from unittest.mock import MagicMock

# 1. Importar el security_monitor de Gravity
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core import security_monitor

print("=> Configurando mocks para simular una amenaza en puerto 9999...")

# Crear objetos mock para simular un proceso sospechoso escuchando en el puerto 9999
mock_conn = MagicMock()
mock_conn.status = "LISTEN"
mock_conn.laddr.port = 9999
mock_conn.pid = 99999

mock_process = MagicMock()
mock_process.info = {
    "pid": 99999,
    "name": "hacker_simulator.exe",
    "ppid": 1,
    "io_counters": None,
}
mock_process.name.return_value = "hacker_simulator.exe"

# Mock para el Anti-Tampering (Cheat Engine simulado)
mock_tampering_process = MagicMock()
mock_tampering_process.info = {
    "pid": 88888,
    "name": "cheatengine-x86_64.exe",
    "ppid": 1,
    "io_counters": None,
}

# Mock de psutil inyectado directamente en el security_monitor
mock_psutil = MagicMock()
mock_psutil.net_connections.return_value = [mock_conn]
# Devolver el mock original para pids, y el nuevo solo cuando itera todos
mock_psutil.Process.return_value = mock_process
mock_psutil.process_iter.return_value = [mock_process, mock_tampering_process]

security_monitor.psutil = mock_psutil
security_monitor._PSUTIL_OK = True
security_monitor._started = True

print("=> Ejecutando escaneo forzado del IPS...")
state = security_monitor.force_scan()

print("=> Resultados del Escaneo:")
action_triggered = False
for alert in state.get("alerts", []):
    if "ACTION" in alert.get("level", "") and "9999" in alert.get("message", ""):
        print(f"[{alert['level']}] {alert['message']}")
        action_triggered = True

print("=> Verificando si la defensa activa mató el proceso sospechoso de puerto...")
if mock_process.kill.called:
    print(
        "[ÉXITO] El proceso simulado (PID 99999) fue ANIQUILADO por la defensa activa (kill() llamado)."
    )
else:
    print(
        "[FALLO] La defensa activa NO llamó a kill() sobre el proceso de red sospechoso."
    )
    sys.exit(1)

print("=> Verificando si el Anti-Tampering detectó y mató la herramienta prohibida...")
if mock_tampering_process.kill.called:
    print(
        "[ÉXITO] La herramienta prohibida (cheatengine-x86_64.exe, PID 88888) fue ANIQUILADA correctamente."
    )
else:
    print("[FALLO] La defensa Anti-Tampering NO llamó a kill().")
    sys.exit(1)
