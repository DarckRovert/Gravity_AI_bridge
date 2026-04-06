import sys
import os
import time

# Ensure we can import rag.retriever
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from rag.retriever import RAGEmbedder

def test_npu():
    print("\n╔══════════════════════════════════════════════╗")
    print("║  GRAVITY AI — NPU FUNCTIONAL TEST V7.1       ║")
    print("╚══════════════════════════════════════════════╝\n")

    print("[1/2] Detecting NPU Backend...")
    backend = RAGEmbedder.get_backend_name()
    print(f">> Active Backend: {backend.upper()}")
    
    if backend != "onnx_npu":
        print("!! FAILED: NPU model not detected in rag/models/npu_minilm/")
        return

    print("\n[2/2] Generating Embedding on NPU...")
    print(">> Warming up engine (XDNA Tiles)...")
    
    start_time = time.time()
    # First run might be slower due to DML graph compilation
    vec = RAGEmbedder.embed(["Prueba de aceleración NPU Ryzen AI en Gravity Bridge V7.1"])
    end_time = time.time()
    
    print(f"++ Embedding Generated! (Size: {len(vec[0])})")
    print(f"++ Time: {(end_time - start_time)*1000:.2f} ms")
    
    print("\n[SUCCESS] NPU Accelerator is fully functional.")
    print(">> Check your Task Manager while running a large indexing task.")

if __name__ == "__main__":
    test_npu()
