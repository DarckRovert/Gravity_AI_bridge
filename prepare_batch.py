import os
import json
import re

path_en = r"E:\Turtle Wow\Interface\AddOns\pfQuest\db\enUS\quests.lua"
path_es = r"E:\Turtle Wow\Interface\AddOns\pfQuest\db\esES\quests.lua"
path_batch = r"E:\Turtle Wow\Interface\AddOns\pfQuest\batch_1.txt"

def get_full_entry(path, qid):
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()
    pattern = re.compile(rf'\[{qid}\] = \{{(.*?)\}}', re.DOTALL)
    m = pattern.search(content)
    if m:
        return f'[{qid}] = {{{m.group(1)}}}'
    return None

# IDs que sabemos que difieren (ID 1, 5, etc.)
ids_to_translate = [1, 5, 8, 40001, 40002, 40003] # Muestra inicial
# ... Aquí añadiría los IDs detectados en la comparación anterior ...

batch_text = "Traduce estas misiones de WoW al español (esES) para Turtle WoW. Mantén el lore y el formato Lua exacto:\n\n"
for qid in ids_to_translate:
    entry = get_full_entry(path_en, qid)
    if entry:
        batch_text += entry + "\n\n"

with open(path_batch, "w", encoding="utf-8") as f:
    f.write(batch_text)

print(f"Lote de traducción generado en {path_batch}")
