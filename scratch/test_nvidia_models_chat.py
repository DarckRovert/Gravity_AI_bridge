import sys
import os
import json
import urllib.request

sys.path.insert(0, r"F:\Gravity_AI_bridge")
from core import key_manager
key = key_manager.KeyManager.get_key("nvidia")

if not key:
    print("No key found")
    sys.exit(1)

# Probar deepseek-ai/deepseek-v4-pro
payload = {
    "model": "deepseek-ai/deepseek-v4-pro",
    "messages": [{"role": "user", "content": "Hola, ¿quién eres? Responde en una frase."}],
    "stream": False
}
data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(
    "https://integrate.api.nvidia.com/v1/chat/completions",
    data=data,
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
)

print("Probando deepseek-ai/deepseek-v4-pro...")
try:
    with urllib.request.urlopen(req, timeout=45) as r:
        resp = json.loads(r.read().decode())
        print("Respuesta Pro:", resp["choices"][0]["message"]["content"])
except Exception as e:
    print("Error Pro:", e)

# Probar deepseek-ai/deepseek-v4-flash
payload["model"] = "deepseek-ai/deepseek-v4-flash"
data = json.dumps(payload).encode("utf-8")
req = urllib.request.Request(
    "https://integrate.api.nvidia.com/v1/chat/completions",
    data=data,
    headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"}
)

print("Probando deepseek-ai/deepseek-v4-flash...")
try:
    with urllib.request.urlopen(req, timeout=45) as r:
        resp = json.loads(r.read().decode())
        print("Respuesta Flash:", resp["choices"][0]["message"]["content"])
except Exception as e:
    print("Error Flash:", e)
