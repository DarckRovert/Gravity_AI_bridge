import json

with open('F:/gravity-news-portal/src/data/news.json', 'r', encoding='utf-8') as f:
    news = json.load(f)

bad_count = 0
good_count = 0
for n in news:
    if 'Transmisión Clandestina de la Zona Ágora' in n.get('title', ''):
        bad_count += 1
    else:
        good_count += 1
        print(f"GOOD: {n.get('title')}")

print(f'\nTotal: {len(news)} | Good: {good_count} | Bad: {bad_count}')
