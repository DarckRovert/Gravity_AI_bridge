import os
import urllib.request
import sys

MODELS_DIR = r"f:\Gravity_AI_bridge\models"
os.makedirs(MODELS_DIR, exist_ok=True)

url = "https://huggingface.co/unsloth/Llama-3.2-1B-Instruct-GGUF/resolve/main/Llama-3.2-1B-Instruct-Q4_K_M.gguf"
filename = "Llama-3.2-1B-Instruct-Q4_K_M.gguf"
filepath = os.path.join(MODELS_DIR, filename)

if os.path.exists(filepath):
    print(f"[SKIP] {filepath} already exists.")
    sys.exit(0)

print(f"[DOWNLOADING] {url} -> {filepath}")

try:
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req) as response, open(filepath, "wb") as out_file:
        totalsize = int(response.info().get("Content-Length", -1))
        readsofar = 0
        blocksize = 8192 * 4

        while True:
            buffer = response.read(blocksize)
            if not buffer:
                break
            readsofar += len(buffer)
            out_file.write(buffer)
            if totalsize > 0 and readsofar % (blocksize * 500) == 0:
                percent = readsofar * 100 / totalsize
                print(f"\r{percent:.1f}% ({readsofar/(1024*1024):.1f} MB / {totalsize/(1024*1024):.1f} MB)", end="")
    print(f"\n[DONE] {filepath}")
except Exception as e:
    print(f"\n[ERROR] Failed to download {url}: {e}")
