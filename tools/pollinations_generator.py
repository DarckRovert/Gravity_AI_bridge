"""
Gravity AI Bridge V13.0 PRO — Pollinations.ai Image Generator
Tool: pollinations_generator
API: https://image.pollinations.ai/prompt/{prompt}

Motor sin estado, sin API key, sin dependencias externas.
Retorna imágenes PNG directamente vía HTTP GET.
Tiempo promedio: 20-60 segundos por imagen.
Máximo resolución: 1440x1440.
"""

import urllib.request
import urllib.parse
import urllib.error
import os
import sys
import time
import hashlib
import io

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# ─── Constants ────────────────────────────────────────────────────────────────

POLLINATIONS_BASE = "https://image.pollinations.ai/prompt/{prompt}"
DEFAULT_MODEL     = "flux"        # flux | turbo | dreamshaper
DEFAULT_TIMEOUT   = 120           # segundos máximos de espera por imagen
MAX_RETRIES       = 3
RETRY_DELAY       = 5.0          # segundos entre reintentos


# ─── Core ─────────────────────────────────────────────────────────────────────

def generate(
    prompt: str,
    output_path: str,
    width: int = 1216,
    height: int = 832,
    model: str = DEFAULT_MODEL,
    seed: int | None = None,
    enhance: bool = True,
    nologo: bool = True,
    negative_prompt: str = "",
) -> dict:
    """
    Genera una imagen usando Pollinations.ai y la guarda en output_path.

    Parámetros
    ----------
    prompt          : Descripción de la imagen en inglés.
    output_path     : Ruta absoluta donde guardar el PNG resultante.
    width           : Ancho en píxeles (max 1440).
    height          : Alto en píxeles (max 1440).
    model           : Motor generativo (flux|turbo|dreamshaper).
    seed            : Semilla reproducible. None = aleatorio.
    enhance         : Pollinations aplica mejoras automáticas al prompt.
    nologo          : Elimina el watermark de Pollinations.
    negative_prompt : Lo que NO quieres que aparezca en la imagen.

    Retorna
    -------
    dict con campos: success (bool), path (str|None), error (str|None)
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # Determinar seed reproducible basado en el prompt si no se provee
    if seed is None:
        seed = int(hashlib.md5(prompt.encode()).hexdigest()[:8], 16) % 2147483647

    encoded_prompt = urllib.parse.quote(prompt.strip(), safe="")
    params = {
        "width":   str(width),
        "height":  str(height),
        "model":   model,
        "seed":    str(seed),
        "enhance": "true" if enhance else "false",
        "nologo":  "true" if nologo else "false",
    }
    if negative_prompt:
        params["nologo"] = "true"  # Ensure nologo stays valid or map it
        # Unfortunately Pollinations does not support negative prompt directly in recent API, 
        # so we inject it logically into the prompt text to guide the model.
        # Alternatively, pollinations respects "negative" or "negative_prompt" query params 
        # occasionally depending on backend. We try both.
        # Another trick is modifying the prompt: "prompt text. Avoid: negative_prompt."
        prompt = f"{prompt.strip()}. Avoid, do not include, exclude: {negative_prompt.strip()}."
    
    encoded_prompt = urllib.parse.quote(prompt.strip(), safe="")
    query = "&".join(f"{k}={urllib.parse.quote(str(v))}" for k, v in params.items())
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?{query}"

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(
                f"[Pollinations] Intento {attempt}/{MAX_RETRIES} — {prompt[:60]}...",
                file=sys.stderr
            )
            req = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "GravityBridge/10.2 (image-pipeline)",
                    "Accept":     "image/png,image/*,*/*",
                }
            )
            with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as resp:
                content_type = resp.getheader("Content-Type", "")
                data = resp.read()

            if not data:
                raise ValueError("Respuesta vacía recibida de Pollinations.")

            if "image" not in content_type and not data.startswith(b"\x89PNG"):
                raise ValueError(f"Respuesta no es imagen. Content-Type={content_type}")

            with open(output_path, "wb") as f:
                f.write(data)

            size_kb = len(data) / 1024
            print(
                f"[Pollinations] OK — {size_kb:.1f} KB → {os.path.basename(output_path)}",
                file=sys.stderr
            )
            return {"success": True, "path": output_path, "error": None}

        except urllib.error.HTTPError as e:
            err = f"HTTP {e.code}: {e.reason}"
        except urllib.error.URLError as e:
            err = f"URLError: {e.reason}"
        except TimeoutError:
            err = "Timeout: Pollinations tardó más de 120 segundos."
        except Exception as e:
            err = str(e)

        print(f"[Pollinations] Error en intento {attempt}: {err}", file=sys.stderr)
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY)

    return {"success": False, "path": None, "error": err}


def health_check() -> dict:
    """Verifica conectividad con Pollinations.ai."""
    try:
        req = urllib.request.Request(
            "https://image.pollinations.ai/",
            headers={"User-Agent": "GravityBridge/10.2"},
            method="HEAD"
        )
        with urllib.request.urlopen(req, timeout=10):
            return {"online": True, "message": "Pollinations.ai accesible."}
    except Exception as e:
        return {"online": False, "message": f"Pollinations.ai sin respuesta: {e}"}


# ─── CLI ──────────────────────────────────────────────────────────────────────

def main():
    """
    Uso CLI: python pollinations_generator.py "prompt" output.png [width] [height]
    """
    if len(sys.argv) < 3:
        import json
        print(json.dumps({"success": False, "error": "Args: prompt output.png [width] [height]"}))
        sys.exit(1)

    prompt      = sys.argv[1]
    output_path = sys.argv[2]
    width       = int(sys.argv[3]) if len(sys.argv) > 3 else 1216
    height      = int(sys.argv[4]) if len(sys.argv) > 4 else 832

    result = generate(prompt, output_path, width, height)

    import json
    print(json.dumps(result))
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
