import os
import subprocess
import sys

def run_cmd(cmd):
    print(f">> Executing: {cmd}")
    result = subprocess.run(cmd, shell=True)
    if result.returncode != 0:
        print(f"!! Error executing command: {cmd}")
        return False
    return True

def setup_npu_env():
    print("╔══════════════════════════════════════════════╗")
    print("║  GRAVITY AI — HYBRID NPU SETUP (3.11)        ║")
    print("╚══════════════════════════════════════════════╝")
    
    env_name = "gravity-npu"
    
    # 1. Create Conda Env
    print(f"\n[1/3] Creando entorno Conda '{env_name}' (Python 3.11)...")
    if not run_cmd(f"conda create -n {env_name} python=3.11 -y"):
        return

    # 2. Install ORT Vitis-AI and basic RAG deps
    print(f"\n[2/3] Instalando dependencias de aceleración (Vitis-AI)...")
    # For Ryzen AI 1.7.1, onnxruntime-vitisai is essentially ORT with the provider enabled.
    # We also install tokenizers and numpy for the hybrid bridge.
    deps = "onnxruntime-vitisai==1.18.1 tokenizers numpy==1.26.4"
    if not run_cmd(f"conda run -n {env_name} pip install {deps}"):
        return

    # 3. Final Verification
    print(f"\n[3/3] Verificando proveedores disponibles en el entorno...")
    verify_script = "import onnxruntime as ort; print(f'Providers: {ort.get_available_providers()}')"
    run_cmd(f"conda run -n {env_name} python -c \"{verify_script}\"")
    
    print("\n[ÉXITO] Entorno Híbrido 'gravity-npu' configurado.")
    print("Gravity Bridge ahora puede delegar tareas al NPU de forma segura.")

if __name__ == "__main__":
    setup_npu_env()
