import time
import subprocess
import random
import os
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPORTER_SCRIPT = os.path.join(BASE_DIR, "gravity_reporter.py")

print("======================================================================")
print("  Gravity AI - Reportero Autonomo (Modo Daemon Continuo)              ")
print("======================================================================")
print("[*] Este agente estara despierto en segundo plano buscando, analizando")
print("[*] y publicando noticias 100% reales en tu portal de manera autonoma.")

# El primer ciclo arranca mas rápido para que el usuario pueda ver actividad (ej. en 10 minutos)
# Luego, los siguientes ciclos seran cada 4 a 8 horas.
is_first_run = True

while True:
    if is_first_run:
        wait_mins = 10
        print(f"\n[*] El agente esta analizando el panorama mundial. Iniciara en {wait_mins} minutos...")
        time.sleep(wait_mins * 60)
        is_first_run = False
    
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Iniciando ciclo de investigacion periodistica...")
    
    try:
        subprocess.run(["python", REPORTER_SCRIPT], cwd=BASE_DIR)
    except Exception as e:
        print(f"Error ejecutando el reportero: {e}")
        
    # Calcular proxima ejecucion (ej. entre 4 y 8 horas para mantener el portal actualizado pero no spamear)
    wait_hours = random.uniform(4, 8)
    next_run = datetime.fromtimestamp(time.time() + (wait_hours * 3600))
    print(f"\n[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Ciclo completado. El agente periodistico tomara un descanso.")
    print(f"[*] Proxima publicacion programada para: {next_run.strftime('%Y-%m-%d %H:%M:%S')} (en aprox {wait_hours:.1f} horas)")
    
    time.sleep(wait_hours * 3600)
