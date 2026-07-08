import json
import os
import urllib.request
import urllib.parse
import re

portal_dir = 'F:/gravity-news-portal'
essays_json = os.path.join(portal_dir, 'src/data/essays.json')
images_dir = os.path.join(portal_dir, 'public/images')

with open(essays_json, 'r', encoding='utf-8') as f:
    essays = json.load(f)

for essay in essays:
    img_path_rel = essay.get('image', '')
    if img_path_rel.startswith('/images/'):
        img_filename = img_path_rel.replace('/images/', '')
        img_path = os.path.join(images_dir, img_filename)
        
        if not os.path.exists(img_path) or os.path.getsize(img_path) == 0:
            print(f"Missing image: {img_filename} for '{essay.get('title')}'")
            
            # Generate via pollinations
            prefix = "cyberpunk philosophical dark moody"
            safe_title = re.sub(r'[^a-zA-Z0-9\sñÑáéíóúÁÉÍÓÚüÜ,.-]', '', essay.get('title', '')[:120])
            title_encoded = urllib.parse.quote(safe_title.strip(), safe='')
            prefix_encoded = urllib.parse.quote(prefix, safe='')
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
                print(f"Failed: {e}")
