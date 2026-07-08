import json
import glob
import os

with open('F:/gravity-news-portal/src/data/news.json', 'r', encoding='utf-8') as f:
    news = json.load(f)

clean_news = []
bad_ids = []

for n in news:
    if 'Transmisión Clandestina' in n.get('title', ''):
        bad_ids.append(n.get('id'))
        print(f"Borrando (title): {n.get('title')}")
    else:
        # Also check for fictional words in the good ones just in case
        text = (n.get('title', '') + " " + n.get('fullText', '')).lower()
        fiction_words = ['lyra','kaelen','altair','macro-leviatán','jueces sintéticos','protocolo ostrom', 'los sabuesos']
        found = [w for w in fiction_words if w in text]
        if found:
            print(f"Borrando por contaminación {found}: {n.get('title')}")
            bad_ids.append(n.get('id'))
        else:
            clean_news.append(n)

print(f"News: {len(news)} -> {len(clean_news)}")

# Save clean news
with open('F:/gravity-news-portal/src/data/news.json', 'w', encoding='utf-8') as f:
    json.dump(clean_news, f, ensure_ascii=False, indent=2)

# Cleanup images
img_dir = "F:/gravity-news-portal/public/images"
all_images = glob.glob(os.path.join(img_dir, "*"))

deleted_images = 0
for img_path in all_images:
    basename = os.path.basename(img_path)
    # The image name is slugified title.
    if 'transmisin-clandestina' in basename.lower() or 'transmision-clandestina' in basename.lower() or 'transmisi-n-clandestina' in basename.lower():
        os.remove(img_path)
        deleted_images += 1
    else:
        # Check against bad_ids if they match start of slug
        for bid in bad_ids:
            # bid is like "slug-hash"
            if bid and bid.split('-')[0] in basename:
                try:
                    os.remove(img_path)
                    deleted_images += 1
                    break
                except Exception:
                    pass

print(f"Deleted images: {deleted_images}")

# Cleanup local generated files
local_dir = "F:/Gravity_AI_bridge/_noticias_generadas"
# reporter.json doesn't actually save to _noticias_generadas! 
# Let me double check if reporter saves local files. Oh wait, reporter.json doesn't have a "guardar_local" FileSaver node, it only has "publicar_noticia" JSONAppender and GitDeploy.
# If there is no _noticias_generadas, it's fine.
