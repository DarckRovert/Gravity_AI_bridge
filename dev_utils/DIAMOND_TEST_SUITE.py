import subprocess
import os
import sys
import urllib.request
import time

def print_banner(text):
    print("\n" + "="*80)
    print(f" {text}".center(80))
    print("="*80)

def run_test(name, cmd):
    print(f"[TEST] {name}...")
    try:
        # Usar encoding utf-8 para capturar caracteres Diamond-Tier
        res = subprocess.run(cmd, shell=True, capture_output=True, text=True, encoding='utf-8')
        if res.returncode == 0:
            print(f"  [PASS] {name} finalizado con exito.\n")
            return True, res.stdout
        else:
            print(f"  [FAIL] {name} fallo con codigo {res.returncode}.\n")
            print(f"  ERROR: {res.stderr}\n")
            return False, res.stderr
    except Exception as e:
        print(f"  [EXCEPTION] {name}: {str(e)}\n")
        return False, str(e)

def check_http(name, url):
    print(f"[TEST] {name} ({url})...")
    try:
        with urllib.request.urlopen(url, timeout=3) as response:
            code = response.getcode()
            if code == 200:
                print(f"  [PASS] {name} online (Status 200).\n")
                return True
            else:
                print(f"  [WARN] {name} respondio con status {code}.\n")
                return False
    except Exception as e:
        print(f"  [INFO] {name} fuera de linea (esperado si el servidor no ha iniciado).\n")
        return False

def verify_all():
    print_banner("GRAVITY AI BRIDGE V9.0 PRO — DIAMOND-TIER AUDIT")
    
    root = "F:/Gravity_AI_bridge"
    
    # 1. Integridad de Archivos
    print("[1] Verificando Archivos Criticos...")
    critical_files = [
        ".antigravityrules", "LICENSE", "config.yaml", 
        "ask_deepseek.py", "bridge_server.py", "dashboard.py",
        "INSTALAR.py", "core/data_guardian.py", "core/hardware_profiler.py",
        "core/provider_manager.py", "core/session_manager.py"
    ]
    for f in critical_files:
        path = os.path.join(root, f)
        if os.path.exists(path):
            print(f"  [OK] {f}")
        else:
            print(f"  [MISSING] {f}")

    # 2. Prueba de Inferencia
    # Nota: Esto requiere que haya un motor (Ollama/LM Studio o API Key) configurado.
    print("\n[2] Ejecutando Inferencia de Prueba (CLI)...")
    success, out = run_test("Inferencia Eco", f"python {root}/ask_deepseek.py \"Escribe 'LOGICA_OK'\"")
    if success:
        if "LOGICA_OK" in out:
            print("  [VERIFIED] El motor de IA responde correctamente.")
        else:
            print("  [WARN] Respuesta recibida pero el 'eco' no fue exacto.")

    # 3. Verificacion de Auditor (Verification Agent)
    print("\n[3] Verificando Agente de Auditoria...")
    run_test("Agente Adversarial", f"python {root}/core/verification_agent.py --help")

    # 4. Salud de Servicios
    print("\n[4] Comprobando Endpoints de Red...")
    check_http("Dashboard Health", "http://localhost:7860/v1/status")
    
    print_banner("FIN DEL AUDIT DIAMOND-TIER")

if __name__ == "__main__":
    verify_all()
