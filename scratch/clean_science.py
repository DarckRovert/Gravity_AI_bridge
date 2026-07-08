import json
import glob
import os

with open('F:/gravity-news-portal/src/data/science.json', 'r', encoding='utf-8') as f:
    science = json.load(f)

clean_science = []
bad_ids = []

for s in science:
    title = s.get('title', '')
    text = (title + " " + s.get('fullText', '')).lower()
    
    if 'transmisión clandestina' in title.lower():
        bad_ids.append(s.get('id'))
        print(f"Borrando (Error): {title}")
    else:
        fiction_words = ['lyra','kaelen','altair','macro-leviatán','jueces sintéticos','protocolo ostrom', 'los sabuesos']
        found = [w for w in fiction_words if w in text]
        if found:
            print(f"Borrando por contaminación {found}: {title}")
            bad_ids.append(s.get('id'))
        else:
            clean_science.append(s)

print(f"Science: {len(science)} -> {len(clean_science)}")

with open('F:/gravity-news-portal/src/data/science.json', 'w', encoding='utf-8') as f:
    json.dump(clean_science, f, ensure_ascii=False, indent=2)

img_dir = "F:/gravity-news-portal/public/images"
all_images = glob.glob(os.path.join(img_dir, "*"))

deleted_images = 0
for img_path in all_images:
    basename = os.path.basename(img_path)
    if 'transmisin-clandestina' in basename.lower() or 'transmision-clandestina' in basename.lower() or 'transmisi-n-clandestina' in basename.lower():
        try:
            os.remove(img_path)
            deleted_images += 1
        except Exception:
            pass
    else:
        for bid in bad_ids:
            if bid and bid.split('-')[0] in basename:
                try:
                    os.remove(img_path)
                    deleted_images += 1
                    break
                except Exception:
                    pass

print(f"Deleted images: {deleted_images}")
