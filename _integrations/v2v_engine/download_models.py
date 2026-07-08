import os
from huggingface_hub import hf_hub_download

MODELS_DIR = os.path.join(os.path.dirname(__file__), "models")
os.makedirs(MODELS_DIR, exist_ok=True)

# Lista de modelos de LivePortrait convertidos a ONNX
# Utilizaremos un repositorio de la comunidad que ya los tenga en ONNX
REPO_ID = "KwaiVGI/LivePortrait" 
ONNX_REPO = "dyicnc/Live-Portrait-ONNX"

# Modelos esenciales para LivePortrait ONNX
onnx_files = [
    "stitching_retargeting_module.onnx",
    "warping_module.onnx"
]

print("[V2V Engine] Descargando pesos ONNX FP16 para LivePortrait (DirectML)...")

for file in onnx_files:
    print(f" -> Descargando {file}...")
    try:
        # Descarga al cache de HF y luego linkea a MODELS_DIR
        path = hf_hub_download(repo_id=ONNX_REPO, filename=file, local_dir=MODELS_DIR, local_dir_use_symlinks=False)
        print(f"    Completado: {path}")
    except Exception as e:
        print(f"    Error descargando {file}: {e}")

print("\n[V2V Engine] Descarga de pesos LivePortrait finalizada.")
