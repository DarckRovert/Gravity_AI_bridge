import json
import os
import urllib.parse

PORTAL_DIR = r"f:\gravity-news-portal"
NEWS_JSON_PATH = os.path.join(PORTAL_DIR, "src", "data", "news.json")
SCIENCE_JSON_PATH = os.path.join(PORTAL_DIR, "src", "data", "science.json")

def fix_images_to_pollinations(file_path, base_prompt):
    if not os.path.exists(file_path):
        return
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    changed = False
    for item in data:
        img_url = item.get("image", "")
        # Si la imagen es de pollinations, hacemos pre-warm
        if "pollinations.ai" in img_url:
            print(f"Pre-calentando: {item.get('title')}")
            try:
                import urllib.request
                req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
                urllib.request.urlopen(req, timeout=45)
                print(f"  [✓] Imagen lista en CDN.")
            except Exception as e:
                print(f"  [!] Falló pre-calentamiento: {e}")

    if changed:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"File {file_path} saved.")

if __name__ == "__main__":
    fix_images_to_pollinations(NEWS_JSON_PATH, "cyberpunk%20news%20dark%20photorealistic")
    fix_images_to_pollinations(SCIENCE_JSON_PATH, "cyberpunk%20science%20dark%20lab")
    print("Done")
