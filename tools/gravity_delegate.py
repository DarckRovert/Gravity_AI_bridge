"""
╔══════════════════════════════════════════════════════════════════════════════╗
║              GRAVITY AI — AGENTIC DELEGATION DISPATCHER V1.0                 ║
║   Permite delegar tareas técnicas y rutinarias a modelos locales y cloud     ║
║       (LM Studio, Groq, Nvidia NIM, etc.) para ahorro masivo de tokens       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import sys
import os
import json
import argparse
import urllib.request
import urllib.error

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from core.logger import log

BRIDGE_URL = "http://127.0.0.1:7860/v1/chat/completions"

def _call_http_bridge(prompt: str, system: str, provider: str, model: str, temperature: float, max_tokens: int) -> dict:
    """Intenta llamar al servidor Gravity Bridge local si está corriendo en :7860."""
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "stream": False,
    }
    if model and model != "auto":
        payload["model"] = model
    if provider and provider != "auto":
        payload["provider"] = provider

    req = urllib.request.Request(
        BRIDGE_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "Gravity-Delegator-Agent/1.0"
        }
    )
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.loads(resp.read().decode("utf-8"))

def _call_inprocess_provider(prompt: str, system: str, provider_name: str, model: str, temperature: float, max_tokens: int) -> str:
    """Ejecuta inferencia directa en el proceso si el servidor HTTP no está activo."""
    from core import provider_manager

    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    opts = {
        "temperature": temperature,
        "max_tokens": max_tokens,
    }

    target_provider = None if (not provider_name or provider_name == "auto") else provider_name
    target_model = None if (not model or model == "auto") else model

    resp = provider_manager.complete_safe(
        messages=messages,
        model=target_model,
        provider=target_provider,
        options=opts,
    )
    if not resp.ok:
        # Fallback de conveniencia: si el target provider está caído (ej. LM Studio cerrado),
        # probar con Groq si tiene API key configurada
        from core.key_manager import KeyManager
        if KeyManager.has_key("groq") and target_provider != "Groq":
            resp_fallback = provider_manager.complete_safe(
                messages=messages,
                model="openai/gpt-oss-20b",
                provider="Groq",
                options=opts,
            )
            if resp_fallback.ok:
                return f"[Fallback Groq (openai/gpt-oss-20b)]: {resp_fallback.text}"
        raise RuntimeError(f"Fallo de inferencia: {resp.error} - {resp.detail}")
    return resp.text

def delegate_task(prompt: str, system: str = "", provider: str = "auto", model: str = "auto", temperature: float = 0.3, max_tokens: int = 2048) -> dict:
    """
    Delega una tarea a Gravity AI.
    Retorna dict con {success: bool, text: str, provider: str, model: str, execution_path: str}
    """
    # 1. Probar HTTP Bridge Server
    try:
        data = _call_http_bridge(prompt, system, provider, model, temperature, max_tokens)
        choices = data.get("choices", [])
        if choices:
            text = choices[0].get("message", {}).get("content", "")
            used_model = data.get("model", model)
            return {
                "success": True,
                "text": text,
                "provider": provider,
                "model": used_model,
                "execution_path": "http_bridge",
            }
    except Exception:
        # Fallback silencioso a llamada in-process
        pass

    # 2. In-Process Direct Engine
    try:
        text = _call_inprocess_provider(prompt, system, provider, model, temperature, max_tokens)
        return {
            "success": True,
            "text": text,
            "provider": provider,
            "model": model,
            "execution_path": "in_process_direct",
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "execution_path": "failed",
        }

def main():
    parser = argparse.ArgumentParser(description="Gravity AI Task Delegator")
    parser.add_argument("prompt", nargs="?", default="", help="Prompt o tarea a delegar")
    parser.add_argument("--file", "-f", help="Ruta a un archivo cuyo contenido será el prompt")
    parser.add_argument("--system", "-s", default="Eres un asistente técnico de alta precisión. Responde directo al punto.", help="System prompt")
    parser.add_argument("--provider", "-p", default="auto", help="Proveedor (LM Studio, Groq, Nvidia NIM, etc.)")
    parser.add_argument("--model", "-m", default="auto", help="Modelo específico")
    parser.add_argument("--temp", "-t", type=float, default=0.2, help="Temperatura")
    parser.add_argument("--max-tokens", type=int, default=2048, help="Máximo de tokens de salida")
    parser.add_argument("--json-out", action="store_true", help="Salida en formato JSON estructurado")

    args = parser.parse_args()

    content = args.prompt
    if args.file and os.path.exists(args.file):
        with open(args.file, "r", encoding="utf-8") as f:
            content = f.read()

    if not content:
        print("Error: Se requiere un prompt o archivo (--file).", file=sys.stderr)
        sys.exit(1)

    res = delegate_task(
        prompt=content,
        system=args.system,
        provider=args.provider,
        model=args.model,
        temperature=args.temp,
        max_tokens=args.max_tokens,
    )

    if args.json_out:
        print(json.dumps(res, indent=2, ensure_ascii=False))
    else:
        if res.get("success"):
            print(res.get("text", ""))
        else:
            print(f"Error delegando tarea: {res.get('error')}", file=sys.stderr)
            sys.exit(1)

if __name__ == "__main__":
    main()
