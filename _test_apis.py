import requests
from core.key_manager import KeyManager

headers_base = {
    "Content-Type": "application/json",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
}

# Test Groq
groq_key = KeyManager.get_key("groq")
try:
    headers = {**headers_base, "Authorization": f"Bearer {groq_key}"}
    r = requests.post(
        "https://api.groq.com/openai/v1/chat/completions",
        headers=headers,
        json={"model": "openai/gpt-oss-20b", "messages": [{"role": "user", "content": "Di solo: OK"}], "max_tokens": 5},
        timeout=10
    )
    if r.status_code == 200:
        msg = r.json()["choices"][0]["message"]
        txt = msg.get("content") or msg.get("reasoning") or ""
        print("Groq OK ->", repr(txt[:50]))
    else:
        print("Groq ERROR:", r.status_code, r.text[:150])
except Exception as e:
    print("Groq exception:", e)

# Test Nvidia
nvidia_key = KeyManager.get_key("nvidia")
try:
    headers = {**headers_base, "Authorization": f"Bearer {nvidia_key}"}
    r = requests.post(
        "https://integrate.api.nvidia.com/v1/chat/completions",
        headers=headers,
        json={"model": "meta/llama-3.2-11b-vision-instruct", "messages": [{"role": "user", "content": "Di solo: OK"}], "max_tokens": 5},
        timeout=15
    )
    if r.status_code == 200:
        print("Nvidia OK ->", r.json()["choices"][0]["message"]["content"])
    else:
        print("Nvidia ERROR:", r.status_code, r.text[:150])
except Exception as e:
    print("Nvidia exception:", e)
