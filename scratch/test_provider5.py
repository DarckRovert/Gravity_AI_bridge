import sys
import os
sys.path.insert(0, r"F:\Gravity_AI_bridge")
from core import provider_manager

topic = "Cómo ChatGPT genera texto que parece humano"
n_scenes = 6

system_prompt = "Eres un director creativo y guionista profesional de cine, documentales y publicidad. Tu objetivo es crear narrativas visuales y auditivas que cautiven al espectador. Responde ÚNICAMENTE con JSON válido, sin texto adicional."
user_prompt = f"Crea un guión de {n_scenes} escenas para un video sobre el siguiente tema o contenido: '{topic}'.\n\nResponde con este JSON exacto:\n{{\n  \"video_title\": \"Un título global\",\n  \"scenes\": [\n    {{\n      \"title\": \"Título\",\n      \"character_anchor\": \"...\",\n      \"image_prompt\": \"...\",\n      \"narration\": \"...\"\n    }}\n  ]\n}}\nGenera exactamente {n_scenes} escenas dentro del array 'scenes'. Solo JSON, nada más."

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user",   "content": user_prompt},
]

print("Calling chat_complete...", flush=True)
try:
    plugin = provider_manager.get_plugin("Nvidia NIM")
    res = plugin.chat_complete(
        messages,
        model="meta/llama-3.3-70b-instruct",
        options={"temperature": 0.7}
    )
    print("Result:", res[:200])
except Exception as e:
    print(f"Exception: {e}")
