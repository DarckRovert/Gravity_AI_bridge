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
        # Si tiene picsum, reemplazar con pollinations
        if "picsum.photos" in img_url:
            title_encoded = urllib.parse.quote(item.get("title", ""))
            new_url = f"https://image.pollinations.ai/prompt/{base_prompt}%20{title_encoded}?width=800&height=600&nologo=true"
            item["image"] = new_url
            changed = True
            print(f"Migrated to Pollinations: {item.get('title')}")

    if changed:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print(f"File {file_path} saved.")

if __name__ == "__main__":
    fix_images_to_pollinations(NEWS_JSON_PATH, "cyberpunk%20news%20dark%20photorealistic")
    fix_images_to_pollinations(SCIENCE_JSON_PATH, "cyberpunk%20science%20dark%20lab")
    print("Done")
