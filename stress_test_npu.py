import sys
import os
import time

# Add root to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from rag.retriever import RAGIndexer, RAGEmbedder

def stress_test():
    print("\n╔══════════════════════════════════════════════╗")
    print("║  GRAVITY AI — NPU FULL WORKSPACE INDEXING    ║")
    print("╚══════════════════════════════════════════════╝\n")

    root = os.path.dirname(os.path.abspath(__file__))
    backend = RAGEmbedder.get_backend_name()
    print(f">> Iniciando indexación global en: {root}")
    print(f">> Acelerador Activo: {backend.upper()}")
    print(">> [AVISO] Abre el Administrador de Tareas (NPU) para ver la actividad.\n")

    start_time = time.time()
    files, chunks = RAGIndexer.index_folder(root)
    end_time = time.time()

    duration = end_time - start_time
    print(f"\n[ÉXITO] Indexación completada.")
    print(f"++ Archivos procesados: {files}")
    print(f"++ Chunks generados:     {chunks}")
    print(f"++ Tiempo total:        {duration:.2f} s")
    if chunks > 0:
        print(f"++ Velocidad media:     {duration/chunks*1000:.2f} ms/chunk")

if __name__ == "__main__":
    stress_test()
