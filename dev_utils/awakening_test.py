import os
import time
import sys

# Ensure project root is in path
BASE_DIR = r"F:\Gravity_AI_bridge"
sys.path.append(BASE_DIR)

from rag.retriever import RAGIndexer

def final_npu_awakening():
    print("╔══════════════════════════════════════════════╗")
    print("║  GRAVITY AI — REAL NPU AWAKENING (VITIS-AI)  ║")
    print("╚══════════════════════════════════════════════╝")
    print("\n>> Hardware Target: AMD Ryzen AI NPU (XDNA)")
    print(">> Provider: VitisAIExecutionProvider")
    print(">> Status: FORCING REAL NEURAL OFFLOADING")
    print("\n[IMPORTANTE] Mira el ADM. DE TAREAS -> Rendimiento -> NPU.")
    print("Debes ver ACTIVIDAD REAL por primera vez.")
    
    start_time = time.time()
    files, chunks = RAGIndexer.index_folder(BASE_DIR)
    end_time = time.time()
    
    total_time = end_time - start_time
    print(f"\n[ÉXITO] Sincronización Neuronal Completada.")
    print(f"++ Archivos: {files}")
    print(f"++ Chunks:   {chunks}")
    print(f"++ Tiempo:   {total_time:.2f} s")
    print(f"++ Latencia: {total_time/chunks*1000:.2f} ms/chunk")
    print("\nSi viste picos en el gráfico de NPU, ¡el despertar ha sido exitoso!")

if __name__ == "__main__":
    final_npu_awakening()
