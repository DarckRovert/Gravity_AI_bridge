import json
import os
import re

PORTAL_DIR = r"f:\gravity-news-portal"
NEWS_JSON_PATH = os.path.join(PORTAL_DIR, "src", "data", "news.json")
SCIENCE_JSON_PATH = os.path.join(PORTAL_DIR, "src", "data", "science.json")

def fix_images(file_path):
    if not os.path.exists(file_path):
        return
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    changed = False
    for item in data:
        img_url = item.get("image", "")
        # Si la imagen tiene el formato /800/600 puro al final y no tiene un '-' (lo que indicaría que ya tiene el ID)
        # O podemos simplemente forzar la reinserción del ID si sabemos que la imagen base existe.
        if "/800/600" in img_url:
            slug_part = item.get("id", "")[:15]
            # Solo actualizar si el slug no está ya inyectado en el URL
            if f"-{slug_part}" not in img_url:
                new_url = img_url.replace("/800/600", f"-{slug_part}/800/600")
                item["image"] = new_url
                changed = True
                print(f"Fixed image for {item.get('title')}: {new_url}")

    if changed:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"File {file_path} saved.")

if __name__ == "__main__":
    fix_images(NEWS_JSON_PATH)
    fix_images(SCIENCE_JSON_PATH)
    print("Done")
