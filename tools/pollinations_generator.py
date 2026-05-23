"""
Gravity AI Bridge — Generador de Imágenes Sin Estado (Pollinations.ai Image Generator)
Estándar: Diamond-Tier (Tipado formal estricto, resiliencia ante red inestable y cero dependencias).
"""
import urllib.request
import urllib.parse
import urllib.error
import os
import sys
import time
import hashlib
import io
from typing import Dict, Any, Optional, List

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

# ─── Constantes del Módulo ───────────────────────────────────────────────────
POLLINATIONS_BASE: str = "https://image.pollinations.ai/prompt/{prompt}"
DEFAULT_MODEL: str = "flux"        # Motores válidos: flux | turbo | dreamshaper
DEFAULT_TIMEOUT: int = 120         # Segundos máximos de tolerancia por imagen
MAX_RETRIES: int = 3
RETRY_DELAY: float = 5.0          # Segundos entre reintentos


def generate(
    prompt: str,
    output_path: str,
    width: int = 1216,
    height: int = 832,
    model: str = DEFAULT_MODEL,
    seed: Optional[int] = None,
    enhance: bool = True,
    nologo: bool = True,
    negative_prompt: str = "",
) -> Dict[str, Any]:
    """
    Genera una imagen usando la API sin estado de Pollinations.ai y la persiste en el disco.

    Parámetros:
        prompt (str): Descripción en inglés de la escena/imagen deseada.
        output_path (str): Ruta de destino absoluta donde se guardará el archivo PNG resultante.
        width (int): Ancho en píxeles (máximo soportado 1440).
        height (int): Alto en píxeles (máximo soportado 1440).
        model (str): Identificador del motor generativo ('flux', 'turbo', 'dreamshaper').
        seed (Optional[int]): Semilla reproducible. Si es None, se autogenera una basada en hash md5 del prompt.
        enhance (bool): Si es True, Pollinations expande y optimiza internamente el prompt.
        nologo (bool): Remueve la marca de agua distintiva si es True.
        negative_prompt (str): Elementos no deseados a excluir de la inferencia.

    Retorna:
        Dict[str, Any]: Diccionario con los campos 'success' (bool), 'path' (Optional[str]) y 'error' (Optional[str]).
    """
    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

    # Determinar semilla numérica determinista basada en el contenido si es aleatorio
    if seed is None:
        seed = int(hashlib.md5(prompt.encode("utf-8")).hexdigest()[:8], 16) % 2147483647

    # Si se suministra prompt negativo, lo concatenamos como instrucción explícita
    if negative_prompt:
        prompt = f"{prompt.strip()}. Avoid, do not include, exclude: {negative_prompt.strip()}."
    
    encoded_prompt: str = urllib.parse.quote(prompt.strip(), safe="")
    params: Dict[str, str] = {
        "width":   str(width),
        "height":  str(height),
        "model":   model,
        "seed":    str(seed),
        "enhance": "true" if enhance else "false",
        "nologo":  "true" if nologo else "false",
    }
    
    query: str = "&".join(f"{k}={urllib.parse.quote(v)}" for k, v in params.items())
    url: str = f"https://image.pollinations.ai/prompt/{encoded_prompt}?{query}"
    err: str = "Desconocido"

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(
                f"[Pollinations] Intento {attempt}/{MAX_RETRIES} — {prompt[:60]}...",
                file=sys.stderr
            )
            req: urllib.request.Request = urllib.request.Request(
                url,
                headers={
                    "User-Agent": "GravityBridge/10.2 (image-pipeline)",
                    "Accept":     "image/png,image/*,*/*",
                }
            )
            with urllib.request.urlopen(req, timeout=DEFAULT_TIMEOUT) as resp:
                content_type: str = resp.getheader("Content-Type", "")
                data: bytes = resp.read()

            if not data:
                raise ValueError("Respuesta vacía recibida desde Pollinations.ai.")

            if "image" not in content_type and not data.startswith(b"\x89PNG"):
                raise ValueError(f"La respuesta de red no es una imagen válida. Content-Type={content_type}")

            with open(output_path, "wb") as f:
                f.write(data)

            size_kb: float = len(data) / 1024
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
            err = f"Timeout: Pollinations tardó más de {DEFAULT_TIMEOUT} segundos."
        except Exception as e:
            err = str(e)

        print(f"[Pollinations] Error en intento {attempt}: {err}", file=sys.stderr)
        if attempt < MAX_RETRIES:
            time.sleep(RETRY_DELAY)

    return {"success": False, "path": None, "error": err}


def health_check() -> Dict[str, Any]:
    """
    Verifica rápidamente la conectividad con los endpoints remotos de Pollinations.ai.

    Retorna:
        Dict[str, Any]: Diagnóstico con 'online' (bool) y 'message' (str).
    """
    try:
        req: urllib.request.Request = urllib.request.Request(
            "https://image.pollinations.ai/",
            headers={"User-Agent": "GravityBridge/10.2"},
            method="HEAD"
        )
        with urllib.request.urlopen(req, timeout=10):
            return {"online": True, "message": "Pollinations.ai accesible."}
    except Exception as e:
        return {"online": False, "message": f"Pollinations.ai sin respuesta: {e}"}


# ─── Interfaz CLI ─────────────────────────────────────────────────────────────

def main() -> None:
    """
    Manejador del punto de entrada CLI.
    Formato de invocación: python pollinations_generator.py "prompt" output.png [width] [height]
    """
    if len(sys.argv) < 3:
        print(json.dumps({"success": False, "error": "Args: prompt output.png [width] [height]"}))
        sys.exit(1)

    prompt: str = sys.argv[1]
    output_path: str = sys.argv[2]
    width: int = int(sys.argv[3]) if len(sys.argv) > 3 else 1216
    height: int = int(sys.argv[4]) if len(sys.argv) > 4 else 832

    result: Dict[str, Any] = generate(prompt, output_path, width, height)
    print(json.dumps(result))
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()

