import json
import os
import urllib.request
import urllib.parse
import re

portal_dir = 'F:/gravity-news-portal'
news_json = os.path.join(portal_dir, 'src/data/news.json')
images_dir = os.path.join(portal_dir, 'public/images')

with open(news_json, 'r', encoding='utf-8') as f:
    news_items = json.load(f)

updated = False

for item in news_items:
    img_val = item.get('image', '')
    title = item.get('title', '')
    item_id = item.get('id', '')
    
    if not item_id:
        continue

    img_filename = f"{item_id}.jpg"
    img_path = os.path.join(images_dir, img_filename)
    
    needs_download = False
    
    if not img_val.startswith('/images/'):
        # It's a raw URL or SVG, we need to download it and update the json
        needs_download = True
        item['image'] = f"/images/{img_filename}"
        updated = True
    else:
        # Check if local file exists
        if not os.path.exists(img_path) or os.path.getsize(img_path) == 0:
            needs_download = True
            
    if needs_download:
        print(f"Missing/remote image for '{title}'")
        
        prefix = "cyberpunk news dark photorealistic"
        safe_title = re.sub(r'[^a-zA-Z0-9\sñÑáéíóúÁÉÍÓÚüÜ,.-]', '', title[:120])
        title_encoded = urllib.parse.quote(safe_title.strip(), safe='')
        prefix_encoded = urllib.parse.quote(prefix, safe='')
        
        # 16:9 for news
        img_url = f"https://image.pollinations.ai/prompt/{prefix_encoded}%20{title_encoded}?width=1200&height=675&nologo=true"
        
        print(f"Downloading from {img_url}")
        try:
            req = urllib.request.Request(img_url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=45) as r:
                if r.status == 200:
                    with open(img_path, "wb") as img_file:
                        img_file.write(r.read())
                    print(f"Saved {img_filename} ({os.path.getsize(img_path)} bytes)")
        except Exception as e:
            print(f"Failed to download image: {e}")

if updated:
    with open(news_json, 'w', encoding='utf-8') as f:
        json.dump(news_items, f, ensure_ascii=False, indent=2)
    print("Updated news.json with local image paths.")
