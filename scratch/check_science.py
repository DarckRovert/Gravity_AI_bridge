import json
import glob
import os

with open('F:/gravity-news-portal/src/data/science.json', 'r', encoding='utf-8') as f:
    science = json.load(f)

bad_count = 0
good_count = 0
for s in science:
    if 'Transmisión Clandestina' in s.get('title', ''):
        bad_count += 1
    else:
        good_count += 1
        print(f"GOOD: {s.get('title')}")

print(f'\nTotal: {len(science)} | Good: {good_count} | Bad: {bad_count}')
