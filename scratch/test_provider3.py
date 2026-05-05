import sys
import os
import json
import urllib.request
sys.path.insert(0, r"F:\Gravity_AI_bridge")
from core import key_manager
key = key_manager.KeyManager.get_key("nvidia")

topic = "Cómo ChatGPT genera texto que parece humano"
n_scenes = 6

system_prompt = "Eres un director creativo y guionista profesional de cine, documentales y publicidad. Tu objetivo es crear narrativas visuales y auditivas que cautiven al espectador. Responde ÚNICAMENTE con JSON válido, sin texto adicional."
user_prompt = f"Crea un guión de {n_scenes} escenas para un video sobre el siguiente tema o contenido: '{topic}'.\n\nResponde con este JSON exacto:\n{{\n  \"video_title\": \"Un título global\",\n  \"scenes\": [\n    {{\n      \"title\": \"Título\",\n      \"character_anchor\": \"...\",\n      \"image_prompt\": \"...\",\n      \"narration\": \"...\"\n    }}\n  ]\n}}\nGenera exactamente {n_scenes} escenas dentro del array 'scenes'. Solo JSON, nada más."

messages = [
    {"role": "system", "content": system_prompt},
    {"role": "user",   "content": user_prompt},
]

payload = {"model": "meta/llama-3.3-70b-instruct", "messages": messages, "stream": True, "temperature": 0.7}
data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request("https://integrate.api.nvidia.com/v1/chat/completions", data=data, headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})

print("Enviando request...", flush=True)
try:
    with urllib.request.urlopen(req, timeout=10) as r:
        for raw in r:
            print("RAW:", raw)
except Exception as e:
    print(f"Exception: {e}")
