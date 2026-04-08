import sys
import os
import json

# Añadir el path del bridge para importar sus módulos
sys.path.append(r"F:\Gravity_AI_bridge")
from ask_deepseek import process_query, AIBridgeConfig

# Cargar el lote
input_json = r"E:\Turtle Wow\Interface\AddOns\pfQuest\turtle_quests_batch1.json"
output_lua = r"E:\Turtle Wow\Interface\AddOns\pfQuest\batch1_es.lua"

with open(input_json, "r", encoding="utf-8") as f:
    batch = json.load(f)

print(f"Traduciendo {len(batch)} misiones...")

# Configuración básica (si es necesaria)
config = AIBridgeConfig()

output_content = "pfDB[\"quests\"][\"esES-turtle\"] = {\n"

for qid, data in batch.items():
    print(f"Traduciendo ID: {qid}...")
    prompt = f"Traduce al español de WoW (esES) para Turtle WoW:\nTítulo: {data.get('T', '')}\nDescripción: {data.get('D', '')}\nObjetivo: {data.get('O', '')}\n\nDevuelve solo el código Lua en el formato: [{qid}] = {{ ['T'] = \"Título\", ['D'] = \"Descripción\", ['O'] = \"Objetivo\" }},"
    
    # Supongamos que process_query devuelve la respuesta del LLM
    # Nota: Si process_query es asíncrona o requiere configuración, ajustar aquí.
    response = process_query(prompt, system_prompt="Eres un traductor experto en WoW Vanilla.")
    
    # Limpiar respuesta (quitar backticks de markdown si los tiene)
    clean_res = response.replace("```lua", "").replace("```", "").strip()
    if clean_res.endswith(","):
        output_content += "  " + clean_res + "\n"
    else:
        output_content += "  " + clean_res + ",\n"

output_content += "}\n"

with open(output_lua, "w", encoding="utf-8") as f:
    f.write(output_content)

print(f"Traducción completada en {output_lua}")
