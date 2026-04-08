import sys
import os
import re

# English source path
en_source = r"C:\Users\darck\.gemini\antigravity\brain\3db1fe6e-709e-4926-8ec9-2db5679b56bd\.system_generated\steps\860\content.md"
# Output ES path
es_out = r"E:\Turtle Wow\Interface\AddOns\pfQuest\db\esES\quests-turtle.lua"

# Bridge path
sys.path.append(r"F:\Gravity_AI_bridge")
from ask_deepseek import process_query

def extract_quests(content):
    # Match [ID] = { ... ["T"] = "Title", ["D"] = "...", ["O"] = "..." }
    pattern = re.compile(r'\[(\d+)\] = \{(.*?)\s*\},', re.DOTALL)
    data = {}
    for qid, body in pattern.findall(content):
        t = re.search(r'\["T"\] = "(.*?)"', body)
        o = re.search(r'\["O"\] = "(.*?)"', body, re.DOTALL)
        d = re.search(r'\["D"\] = "(.*?)"', body, re.DOTALL)
        if t and o and d:
            data[qid] = {"T": t.group(1), "O": o.group(1), "D": d.group(1)}
    return data

with open(en_source, "r", encoding="utf-8") as f:
    content = f.read()

quests = extract_quests(content)
target_ids = sorted(quests.keys(), key=int)[:20] # Probamos con 20 para ver progreso rápido

print(f"Traduciendo {len(target_ids)} misiones...")

es_content = "pfDB[\"quests\"][\"esES-turtle\"] = {\n"
for qid in target_ids:
    q = quests[qid]
    print(f"ID {qid}: {q['T']}")
    prompt = f"Traduce al español esES para WoW Vanilla:\nTítulo: {q['T']}\nObjetivo: {q['O']}\nDescripción: {q['D']}"
    try:
        # Llamada directa al bridge
        res = process_query(prompt, system_prompt="Eres un traductor de Lore de WoW. Devuelve solo un diccionario Lua: ['T']='..', ['O']='..', ['D']='..'")
        # Limpieza básica
        clean = res.replace("```lua", "").replace("```", "").strip()
        es_content += f"  [{qid}] = {clean},\n"
    except Exception as e:
        print(f"Error en {qid}: {e}")

es_content += "}\n"

with open(es_out, "w", encoding="utf-8") as f:
    f.write(es_content)

print(f"Archivo actualizado: {es_out}")
