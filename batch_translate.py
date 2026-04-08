import sys
import os
import re

# Fetch the raw English file content from the step 860 path
input_path = r"C:\Users\darck\.gemini\antigravity\brain\3db1fe6e-709e-4926-8ec9-2db5679b56bd\.system_generated\steps\860\content.md"
output_path = r"E:\Turtle Wow\Interface\AddOns\pfQuest\db\esES\quests-turtle.lua"

def extract_quests(content):
    pattern = re.compile(r'\[(\d+)\] = \{(.*?)\s*\},', re.DOTALL)
    return {qid: data for qid, data in pattern.findall(content)}

with open(input_path, "r", encoding="utf-8") as f:
    content = f.read()

all_quests = extract_quests(content)
target_ids = sorted(all_quests.keys(), key=int)[4:54] # 4 misiones ya hechas, traducimos 50 más

# Importar el Bridge para traducción
sys.path.append(r"F:\Gravity_AI_bridge")
from ask_deepseek import process_query

print(f"Traduciendo lote de 50 misiones...")

results = []
for qid in target_ids:
    data = all_quests[qid]
    t_match = re.search(r'\["T"\] = "(.*?)"', data)
    title = t_match.group(1) if t_match else "Sin Título"
    
    print(f"Traduciendo ID {qid}: {title}")
    prompt = f"Traduce al español de WoW (esES) para Turtle WoW:\nOriginal: {data}\n\nDevuelve solo el código Lua en el formato: [{qid}] = {{ ... }},"
    
    # Intento 2: Llamada directa al Bridge
    try:
        response = process_query(prompt, system_prompt="Eres un traductor experto en WoW Vanilla. Devuelve solo el código Lua traducido.")
        clean_res = response.replace("```lua", "").replace("```", "").strip()
        results.append(clean_res)
    except Exception as e:
        print(f"Error en ID {qid}: {e}")

# Append to file
with open(output_path, "a", encoding="utf-8") as f:
    for res in results:
        if not res.endswith(","): res += ","
        f.write("  " + res + "\n")

print("Lote completado.")
