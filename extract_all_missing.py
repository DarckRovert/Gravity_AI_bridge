import os
import sys
import re

path_en = r"E:\Turtle Wow\Interface\AddOns\pfQuest\db\enUS\quests.lua"
path_es = r"E:\Turtle Wow\Interface\AddOns\pfQuest\db\esES\quests.lua"
path_out = r"E:\Turtle Wow\Interface\AddOns\pfQuest\turtle_quests_en.txt"

def get_all_entries(path):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    # Match [ID] = { ... }
    pattern = re.compile(r'\[(\d+)\] = \{(.*?)\}', re.DOTALL)
    return {int(qid): f'[{qid}] = {{{data}}}' for qid, data in pattern.findall(content)}

print("Cargando bases de datos...")
en_entries = get_all_entries(path_en)
es_entries = get_all_entries(path_es)

missing = []
for qid in sorted(en_entries.keys()):
    if qid not in es_entries:
        missing.append(en_entries[qid])

with open(path_out, "w", encoding="utf-8") as f:
    f.write("\n\n".join(missing))

print(f"Extracción completa: {len(missing)} misiones detectadas en {path_out}")
