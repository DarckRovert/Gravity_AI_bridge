import os
import sys

_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(_BASE, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

try:
    from huggingface_hub import hf_hub_download
except ImportError:
    print("\n[!] Error: huggingface_hub no está instalado.")
    print("Por favor, ejecuta 'pip install huggingface-hub'")
    sys.exit(1)

# Lista de modelos óptimos para Gravity AI y Ryzen 7 8700G
MODELS = [
    {
        "role": "El Especialista (BountyHunter / Scraping)",
        "name": "Qwen2.5-Coder-7B-Instruct-Q5_K_M.gguf",
        "repo": "bartowski/Qwen2.5-Coder-7B-Instruct-GGUF",
        "desc": "Brutal lógica y generación de JSON perfecta.",
    },
    {
        "role": "El Especialista Ligero (Filtraje Ultra Rápido)",
        "name": "Phi-3.5-mini-instruct-Q4_K_M.gguf",
        "repo": "bartowski/Phi-3.5-mini-instruct-GGUF",
        "desc": "Solo 3.8B, no consume casi RAM. Vuela.",
    },
    {
        "role": "El Corrector Estricto (Textos largos)",
        "name": "Hermes-3-Llama-3.1-8B-Q5_K_M.gguf",
        "repo": "bartowski/Hermes-3-Llama-3.1-8B-GGUF",
        "desc": "Obediencia militar al System Prompt. No conversará.",
    },
    {
        "role": "El Lector de Novelas (Corrector de Capítulos)",
        "name": "Mistral-Nemo-Instruct-2407-Q4_K_M.gguf",
        "repo": "bartowski/Mistral-Nemo-Instruct-2407-GGUF",
        "desc": "Memoria masiva de 128k. Ideal para contextos inmensos.",
    },
    {
        "role": "El Inteligente (Razonamiento Humano / General)",
        "name": "gemma-2-9b-it-Q4_K_M.gguf",
        "repo": "bartowski/gemma-2-9b-it-GGUF",
        "desc": "Supera a Llama-3 en lógica compleja. Redacción humana.",
    },
    {
        "role": "El Infiltrador Sin Filtros (Uncensored)",
        "name": "dolphin-2.9-llama3-8b-Q5_K_M.gguf",
        "repo": "cognitivecomputations/dolphin-2.9-llama3-8b-gguf",
        "desc": "Responderá a TODO. Ideal para material no apto para todo público.",
    },
]


def main():
    print("==================================================================")
    print("   GRAVITY AI - DESCARGA DE CEREBROS NATIVOS (GGUF)")
    print("==================================================================")
    print(f"Directorio destino: {MODELS_DIR}\n")

    for i, m in enumerate(MODELS):
        print(f"[{i+1}] {m['role']}")
        print(f"    Archivo : {m['name']}")
        print(f"    Detalle : {m['desc']}")
        print()

    print("[0] Salir")
    print("==================================================================")

    try:
        choice = int(input("Selecciona el número del modelo que quieres descargar: "))
        if choice == 0:
            sys.exit(0)

        if 1 <= choice <= len(MODELS):
            m = MODELS[choice - 1]
            print(f"\n[+] Iniciando descarga de {m['name']} desde {m['repo']}...")
            print("    Dependiendo de tu conexión, esto tomará unos minutos.")
            print("    No cierres esta ventana.\n")

            try:
                # local_dir allows placing it directly without symlinks if desired
                file_path = hf_hub_download(
                    repo_id=m["repo"],
                    filename=m["name"],
                    local_dir=MODELS_DIR,
                    local_dir_use_symlinks=False,
                )
                print("\n[✓] Descarga completada exitosamente!")
                print(f"    Guardado en: {file_path}")
                print(
                    "    Gravity AI lo detectará automáticamente la próxima vez que arranque."
                )
            except Exception as e:
                print(f"\n[!] Error durante la descarga: {e}")
        else:
            print("Opción inválida.")
    except ValueError:
        print("Entrada inválida.")


if __name__ == "__main__":
    main()
