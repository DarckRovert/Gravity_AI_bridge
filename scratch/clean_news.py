import json
import os

portal_dir = 'F:/gravity-news-portal'
news_json = os.path.join(portal_dir, 'src/data/news.json')

with open(news_json, 'r', encoding='utf-8') as f:
    news_items = json.load(f)

# The good articles we want to keep are:
# - "El Leviatán Digital y la Resistencia de los Comunes: Una Síntesis Filosófica"
# - "Detrás de la Cortina: El Caso del Docente de Luxemburgo y la Lucha por la Verdad en un Mundo de Manipulación"
good_titles = [
    "El Leviatán Digital y la Resistencia de los Comunes: Una Síntesis Filosófica",
    "Detrás de la Cortina: El Caso del Docente de Luxemburgo y la Lucha por la Verdad en un Mundo de Manipulación"
]

clean_news = []
for item in news_items:
    title = item.get('title', '')
    if title in good_titles:
        clean_news.append(item)
    else:
        # If there's an image path, remove it locally just in case
        img_path_rel = item.get('image', '')
        if img_path_rel.startswith('/images/'):
            img_path = os.path.join(portal_dir, 'public', img_path_rel.lstrip('/'))
            if os.path.exists(img_path):
                os.remove(img_path)
        print(f"Deleted corrupt news: {title}")

with open(news_json, 'w', encoding='utf-8') as f:
    json.dump(clean_news, f, ensure_ascii=False, indent=2)

print(f"Cleaned news.json. Remaining items: {len(clean_news)}")
