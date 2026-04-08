import sys
sys.path.append(r"F:\Gravity_AI_bridge")
from ask_deepseek import process_query

def translate_one(qid, text):
    prompt = f"Traduce al español de WoW (esES) para Turtle WoW. Devuelve solo el código Lua:\n{text}"
    return process_query(prompt, system_prompt="Eres un traductor de Lore de WoW.")

print("Test de Conectividad con el Bridge...")
try:
    res = translate_one(40001, '[40001] = { ["T"] = "A New Threat", ["O"] = "Kill 6 Spiders", ["D"] = "The spiders are attacking our camp!" }')
    print(f"Respuesta Bridge: {res}")
except Exception as e:
    print(f"Error Bridge: {e}")
