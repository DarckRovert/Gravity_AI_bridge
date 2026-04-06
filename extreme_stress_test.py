import os
import time
import sys
import numpy as np
import onnxruntime as ort

# Ensure project root is in path
BASE_DIR = r"F:\Gravity_AI_bridge"
sys.path.append(BASE_DIR)

def extreme_npu_stress():
    print("╔══════════════════════════════════════════════╗")
    print("║   STRESS TEST EXTREMO: DESPERTAR DEL NPU     ║")
    print("╚══════════════════════════════════════════════╝")
    print("\n[CONFIG] Target: AMD Ryzen AI (XDNA)")
    print("[CONFIG] Motor: VitisAIExecutionProvider")
    print("[CONFIG] Carga: 10,000 Chunks continuos (~60-90 segs)")
    print("\n>> MIRA EL GRÁFICO DE NPU AHORA <<")

    npu_dir = os.path.join(BASE_DIR, "rag", "models", "npu_minilm")
    model_path = os.path.join(npu_dir, "model_int8.onnx")
    install_dir = r"C:\Program Files\RyzenAI\1.7.1"
    xclbin_path = os.path.join(install_dir, "voe-4.0-win_amd64", "xclbins", "phoenix", "4x4.xclbin")

    providers = [
        ('VitisAIExecutionProvider', {
            'target': 'X1',
            'xclbin': xclbin_path,
            'config_file': ''
        })
    ]

    # Verbose logging to confirm node placement
    session_options = ort.SessionOptions()
    session_options.log_severity_level = 0 # Verbose

    try:
        session = ort.InferenceSession(model_path, sess_options=session_options, providers=providers)
        print("\n[STATUS] Sesión Neuronal Inicializada.")
    except Exception as e:
        print(f"\n[ERROR] Fallo al inicializar Vitis-AI: {e}")
        return

    # Dummy data 1x128
    input_ids = np.zeros((1, 128), dtype=np.int64)
    attn_mask = np.ones((1, 128), dtype=np.int64)
    token_type = np.zeros((1, 128), dtype=np.int64)
    feed = {
        "input_ids": input_ids, 
        "attention_mask": attn_mask,
        "token_type_ids": token_type
    }

    print("\n>> INICIANDO SATURACIÓN NEURONAL...")
    start_time = time.time()
    
    # Loop for sustained activity
    for i in range(10000):
        session.run(None, feed)
        if i % 1000 == 0:
            print(f"++ Progreso: {i}/10000 chunks procesados...")

    end_time = time.time()
    total_time = end_time - start_time
    
    print(f"\n[ÉXITO] Prueba Finalizada.")
    print(f"++ Tiempo Total: {total_time:.2f} s")
    print(f"++ Rendimiento NPU: {10000/total_time:.2f} chunks/sec")
    print("\nSi el gráfico no se movió, reporta el log anterior.")

if __name__ == "__main__":
    extreme_npu_stress()
