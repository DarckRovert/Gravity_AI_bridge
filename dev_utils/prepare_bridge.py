import json
import os

input_json = r"E:\Turtle Wow\Interface\AddOns\pfQuest\turtle_quests_batch1.json"
prompt_file = r"E:\Turtle Wow\Interface\AddOns\pfQuest\bridge_prompt.txt"

with open(input_json, "r", encoding="utf-8") as f:
    batch = json.load(f)

# Format for the Bridge: ID: Title | Objective | Description
prompt_text = "Traduce estas misiones de Turtle WoW al español (esES). Mantén un tono épico y técnico. Formatea la salida como una tabla Lua válida para pfQuest:\n\n"
for qid, data in batch.items():
    prompt_text += f"ID: {qid}\n"
    prompt_text += f"T: {data.get('T', '')}\n"
    prompt_text += f"O: {data.get('O', '')}\n"
    prompt_text += f"D: {data.get('D', '')}\n\n"

with open(prompt_file, "w", encoding="utf-8") as f:
    f.write(prompt_text)

print(f"Prompt de traducción generado en {prompt_file}")
