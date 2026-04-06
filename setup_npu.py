import os
import sys
import subprocess
import urllib.request
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, "rag", "models", "npu_minilm")
os.makedirs(MODEL_DIR, exist_ok=True)

def run_cmd(cmd):
    print(f">> Executing: {cmd}")
    try:
        subprocess.check_call([sys.executable, "-m"] + cmd)
        return True
    except Exception as e:
        print(f"!! Error: {e}")
        return False

def download_file(url, filename):
    path = os.path.join(MODEL_DIR, filename)
    if os.path.exists(path):
        print(f"-- Already exists: {filename}")
        return path
    print(f">> Downloading: {filename}...")
    try:
        urllib.request.urlretrieve(url, path)
        print(f"++ Saved to: {path}")
        return path
    except Exception as e:
        print(f"!! Failed to download {filename}: {e}")
        return None

def main():
    print("\n╔══════════════════════════════════════════════╗")
    print("║  GRAVITY AI — NPU ACTIVATION BOOTSTRAP V7.1  ║")
    print("╚══════════════════════════════════════════════╝\n")

    # 1. Install dependencies
    # Using DirectML for wide NPU compatibility on Windows 11
    print("[1/3] Instaling ONNX Runtime (DirectML)...")
    if not run_cmd(["pip", "install", "onnxruntime-directml", "numpy", "tokenizers"]):
        print("!! Failed to install dependencies. Check your internet connection.")
        return

    # 2. Download Model (all-MiniLM-L6-v2 ONNX)
    print("\n[2/3] Downloading Optimized ONNX Model for NPU...")
    files = {
        "model.onnx":     "https://huggingface.co/Xenova/all-MiniLM-L6-v2/resolve/main/onnx/model.onnx",
        "tokenizer.json": "https://huggingface.co/Xenova/all-MiniLM-L6-v2/resolve/main/tokenizer.json",
        "config.json":    "https://huggingface.co/Xenova/all-MiniLM-L6-v2/resolve/main/config.json"
    }
    
    for name, url in files.items():
        if not download_file(url, name):
            print("!! Aborting: Missing critical model file.")
            return

    # 3. Create metadata
    with open(os.path.join(MODEL_DIR, "metadata.json"), "w") as f:
        json.dump({"model": "all-MiniLM-L6-v2", "format": "onnx", "optimized": True}, f)

    print("\n[3/3] NPU Backend Prepared Successfully.")
    print(">> Target: AMD Ryzen AI NPU via DirectML Provider.")
    print("\n[SUCCESS] Ready for integration into rag/retriever.py\n")

if __name__ == "__main__":
    main()
