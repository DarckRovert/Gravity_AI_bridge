import os
import urllib.request
import time

MODELS_DIR = r"f:\Gravity_AI_bridge\models"
os.makedirs(MODELS_DIR, exist_ok=True)

MODELS_TO_DOWNLOAD = [
    {
        "url": "https://huggingface.co/nomic-ai/nomic-embed-text-v1.5-GGUF/resolve/main/nomic-embed-text-v1.5.f16.gguf",
        "filename": "nomic-embed-text-v1.5.f16.gguf"
    },
    {
        "url": "https://huggingface.co/xtuner/llava-phi-3-mini-gguf/resolve/main/llava-phi-3-mini-mmproj-f16.gguf",
        "filename": "llava-phi-3-mini-mmproj-f16.gguf"
    },
    {
        "url": "https://huggingface.co/xtuner/llava-phi-3-mini-gguf/resolve/main/llava-phi-3-mini-int4.gguf",
        "filename": "llava-phi-3-mini-int4.gguf"
    }
]

def download_file(url, filepath):
    if os.path.exists(filepath):
        print(f"[SKIP] {filepath} already exists.")
        return
    print(f"[DOWNLOADING] {url} -> {filepath}")
    
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req) as response, open(filepath, 'wb') as out_file:
            totalsize = int(response.info().get('Content-Length', -1))
            readsofar = 0
            blocksize = 8192
            
            while True:
                buffer = response.read(blocksize)
                if not buffer:
                    break
                readsofar += len(buffer)
                out_file.write(buffer)
                if totalsize > 0 and readsofar % (blocksize * 500) == 0:
                    percent = readsofar * 100 / totalsize
                    print(f"\r{percent:.1f}% ({readsofar/(1024*1024):.1f} MB)", end="")
        print(f"\n[DONE] {filepath}")
    except Exception as e:
        print(f"\n[ERROR] Failed to download {url}: {e}")

for item in MODELS_TO_DOWNLOAD:
    dest = os.path.join(MODELS_DIR, item["filename"])
    download_file(item["url"], dest)

print("\nAll downloads finished!")
