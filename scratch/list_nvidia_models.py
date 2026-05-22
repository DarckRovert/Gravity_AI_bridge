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

req = urllib.request.Request(
    "https://integrate.api.nvidia.com/v1/models",
    headers={"Authorization": f"Bearer {key}"}
)

try:
    with urllib.request.urlopen(req, timeout=10) as r:
        data = json.loads(r.read().decode())
        ids = sorted([model["id"] for model in data.get("data", [])])
        for model_id in ids:
            print(model_id)
except Exception as e:
    print("Error:", e)

