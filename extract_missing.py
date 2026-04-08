import os
import sys
import json

path_en = r"E:\Turtle Wow\Interface\AddOns\pfQuest\db\enUS\quests.lua"
path_es = r"E:\Turtle Wow\Interface\AddOns\pfQuest\db\esES\quests.lua"
path_out = r"E:\Turtle Wow\Interface\AddOns\pfQuest\missing_quests.json"

def extract_titles(path):
    titles = {}
    if not os.path.exists(path): return titles
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    import re
    # Match [ID] = { ... ["T"] = "Title" ... }
    pattern = re.compile(r'\[(\d+)\] = \{.*?\["T"\] = "(.*?)".*?\}', re.DOTALL)
    for qid, title in pattern.findall(content):
        titles[int(qid)] = title
    return titles

print("Analizando bases de datos...")
en_titles = extract_titles(path_en)
es_titles = extract_titles(path_es)

missing = {}
for qid, title in en_titles.items():
    if qid not in es_titles:
        missing[qid] = title

print(f"Detectadas {len(missing)} misiones faltantes en español.")

# Guardar solo las primeras 50 para el primer lote (evitar saturación)
batch = {str(k): v for k, v in list(missing.items())[:50]}
with open(path_out, "w", encoding="utf-8") as f:
    json.dump(batch, f, indent=4)

print(f"Lote de 50 misiones guardado en {path_out}")
