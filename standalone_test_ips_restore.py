import subprocess
import time
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from core import security_monitor

target_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ask_deepseek.py")

# 1. Asegurar estado limpio inicial y capturar baseline
print("=> Limpiando archivo con git checkout previo...")
subprocess.run(["git", "checkout", "ask_deepseek.py"], check=True)

print("=> Inicializando monitor (Baseline de Hashes)...")
security_monitor._started = False
security_monitor.start()
time.sleep(1) # Dar tiempo al thread para calcular hashes

# 2. Inyectar código malicioso
print("=> Inyectando código malicioso en ask_deepseek.py...")
with open(target_file, "a", encoding="utf-8") as f:
    f.write("\n# INYECCIÓN MALICIOSA TEST IPS\n")

# 3. Forzar el escaneo del IPS
print("=> Ejecutando escaneo forzado del IPS...")
state = security_monitor.force_scan()

# 4. Resultados
print("\n=> Alertas Registradas:")
for alert in state.get("alerts", []):
    if "ask_deepseek" in alert.get("message", "") or "ACTION" in alert.get("level", ""):
        print(f"[{alert['level']}] {alert['message']}")

print("\n=> Integridad del Archivo Reportada:")
print(state.get("file_integrity", {}).get("ask_deepseek.py"))

print("\n=> Verificando archivo físicamente...")
with open(target_file, "r", encoding="utf-8") as f:
    content = f.read()
    if "INYECCIÓN MALICIOSA TEST IPS" in content:
        print("[FALLO] El archivo sigue infectado!")
    else:
        print("[ÉXITO] Gravity purgo la infección y restauró el archivo con éxito.")

