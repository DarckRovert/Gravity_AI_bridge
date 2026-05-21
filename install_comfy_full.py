import os
import urllib.request
import py7zr
import shutil
import subprocess

BASE_DIR = r"f:\Gravity_AI_bridge\_integrations"
COMFY_URL = "https://github.com/Comfy-Org/ComfyUI/releases/download/v0.20.1/ComfyUI_windows_portable_nvidia.7z"
MODEL_URL = "https://huggingface.co/Lightricks/LTX-Video/resolve/main/ltx-video-2b-v0.9.5.safetensors"
COMFY_7Z = os.path.join(BASE_DIR, "ComfyUI_portable.7z")
EXTRACT_PATH = os.path.join(BASE_DIR, "ComfyUI_windows_portable")

def download_file(url, path):
    print(f"Downloading {url} to {path}...")
    def report(block_num, block_size, total_size):
        read_so_far = block_num * block_size
        if total_size > 0:
            percent = read_so_far * 100 / total_size
            if block_num % 1000 == 0:
                print(f"Downloaded {percent:.2f}%")
        else:
            if block_num % 1000 == 0:
                print(f"Downloaded {read_so_far / 1024 / 1024:.2f} MB")
    
    urllib.request.urlretrieve(url, path, reporthook=report)
    print("Download complete.")

def main():
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)

    # 1. Download ComfyUI
    if not os.path.exists(EXTRACT_PATH):
        if not os.path.exists(COMFY_7Z):
            download_file(COMFY_URL, COMFY_7Z)
        
        print(f"Extracting {COMFY_7Z} using 7zr.exe...")
        exe_7z = os.path.join(BASE_DIR, "7zr.exe")
        subprocess.run([exe_7z, "x", COMFY_7Z, f"-o{BASE_DIR}", "-y"], check=True)
        print("Extraction complete.")
        # The extraction usually creates a folder like 'ComfyUI_windows_portable'
        # Let's check if it matches EXTRACT_PATH. If it created another name, we might need to rename.
    else:
        print("ComfyUI already extracted.")

    # 2. Download Model
    model_dest = os.path.join(EXTRACT_PATH, "ComfyUI", "models", "checkpoints", "ltx-video-2b-v0.9.5.safetensors")
    os.makedirs(os.path.dirname(model_dest), exist_ok=True)
    if not os.path.exists(model_dest):
        download_file(MODEL_URL, model_dest)
    else:
        print("Model already exists.")

    # 3. Install Custom Nodes
    print("Installing LTX-Video custom nodes...")
    installer_bat = r"f:\Gravity_AI_bridge\launchers\Instalar_Modulo_Video_LTX.bat"
    if os.path.exists(installer_bat):
        subprocess.run([installer_bat], shell=True)
    else:
        print("Installer bat not found.")

    print("ALL DONE!")

if __name__ == "__main__":
    main()
