"""
Gravity AI Bridge V9.3.1 PRO — Fooocus (CPU) Satellite Client
Tool: fooocus_client
Endpoint: http://127.0.0.1:7861 (Fooocus HTTP API — modo CPU)
Hardware: AMD Ryzen 7 8700G — CPU puro (sin DirectML, sin crash)
Motor: Fooocus 2.5.5 (F:\\Gravity_AI_bridge\\_integrations\\Fooocus)

NOTA: Fooocus se lanza con --always-cpu --all-in-fp32 para compatibilidad
      total en cualquier hardware. Sampler: euler (CPU-safe).
      Generacion: 3-8 min por imagen (Ryzen 7 8700G, 30 steps SDXL).
"""

import os
import json
import time
import urllib.request
import urllib.error
from typing import TypedDict, Literal

# ─── Constants ────────────────────────────────────────────────────────────────

FOOOCUS_BASE_URL: str = os.getenv("FOOOCUS_URL", "http://127.0.0.1:7861")

# Output dir de Fooocus: donde graba las imagenes generadas
OUTPUT_DIR: str = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "_integrations", "Fooocus", "Fooocus", "outputs")
)

PERFORMANCE_MAP: dict = {
    "Speed":   "Speed",
    "Quality": "Quality",
    "Extreme Speed": "Extreme Speed",
    "Lightning": "Lightning",
}

# ─── TypedDicts ───────────────────────────────────────────────────────────────

class ImageGenRequest(TypedDict, total=False):
    prompt: str
    negative_prompt: str
    width: int
    height: int
    num_images: int
    performance: Literal["Speed", "Quality", "Extreme Speed", "Lightning"]
    style_selections: list
    reference_image_path: object


class ImageGenResponse(TypedDict):
    success: bool
    images: list
    error: object
    job_id: object


class HealthStatus(TypedDict):
    online: bool
    version: object
    message: str


# ─── Health Check ─────────────────────────────────────────────────────────────

def health_check() -> HealthStatus:
    """
    Verifica si Fooocus responde en el puerto configurado.
    Fooocus 2.5.5 en este build expone UI Gradio (no API REST).
    Detectamos disponibilidad intentando conectar al root de Gradio.
    """
    try:
        req = urllib.request.Request(
            FOOOCUS_BASE_URL,
            method="GET",
            headers={"User-Agent": "GravityBridge/9.2"},
        )
        with urllib.request.urlopen(req, timeout=5) as r:
            if r.status == 200:
                return {"online": True, "version": "Fooocus 2.5.5 (CPU)", "message": "Fooocus UI activa."}
    except urllib.error.HTTPError as e:
        # Cualquier respuesta HTTP (incluso errores) significa que Fooocus está corriendo
        if e.code < 500:
            return {"online": True, "version": "Fooocus 2.5.5 (CPU)", "message": f"Fooocus activo (HTTP {e.code})."}
    except Exception as e:
        return {
            "online": False,
            "version": None,
            "message": f"Fooocus offline. Ejecuta launchers\\INICIAR_TODO.bat. Error: {e}"
        }
    return {"online": False, "version": None, "message": "Fooocus sin respuesta."}


# ─── Image Generation ─────────────────────────────────────────────────────────

def generate_image(request: ImageGenRequest) -> ImageGenResponse:
    """
    Envia una peticion de generacion a Fooocus via su API HTTP.
    Usa sampler 'euler' (CPU-safe, sin crash en DirectML).
    Devuelve job_id para polling posterior.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    prompt_text: str  = request.get("prompt", "")
    neg_prompt: str   = request.get("negative_prompt", "ugly, deformed, blurry, low quality, watermark")
    width: int        = request.get("width", 832)
    height: int       = request.get("height", 1216)
    batch: int        = request.get("num_images", 1)
    # Speed usa euler (CPU-safe). Evitar Extreme Speed / Lightning que activan LoRAs GPU-only
    performance: str  = PERFORMANCE_MAP.get(request.get("performance", "Speed"), "Speed")  # type: ignore
    styles: list      = request.get("style_selections", ["Fooocus V2", "Fooocus Enhance"])

    payload: dict = {
        "prompt":                  prompt_text,
        "negative_prompt":         neg_prompt,
        "style_selections":        styles if styles else ["Fooocus V2", "Fooocus Enhance"],
        "performance_selection":   performance,
        "aspect_ratios_selection": f"{width}\u00d7{height}",
        "image_number":            batch,
        "image_seed":              -1,
        "sharpness":               2.0,
        "guidance_scale":          7.0,
        "base_model_name":         "juggernautXL_v8Rundiffusion.safetensors",
        "refiner_model_name":      "None",
        "refiner_switch":          0.8,
        "loras":                   [],
        "advanced_params": {
            "adaptive_cfg":      7.0,
            # Sampler CPU-safe: euler no requiere kernels GPU-only (evita RuntimeError)
            "sampler_name":      "euler",
            "scheduler_name":    "normal",
            "overwrite_step":    30,
            "overwrite_switch":  -1,
        },
        "save_extension":  "png",
        "save_meta_json":  False,
        "require_base64":  False,
        "async_process":   True,
        "output_format":   "png",
    }

    payload_data = json.dumps(payload).encode("utf-8")

    try:
        req = urllib.request.Request(
            f"{FOOOCUS_BASE_URL}/v1/generation/text-to-image",
            data=payload_data,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=30) as response:
            res_data = json.loads(response.read())
            job_id = res_data.get("job_id")
            return {"success": True, "images": [], "error": None, "job_id": job_id}
    except Exception as e:
        return {"success": False, "images": [], "error": f"API Error: {e}", "job_id": None}


# ─── Job Status Polling ───────────────────────────────────────────────────────

def poll_job(job_id: str, timeout: int = 600, poll_interval: int = 5) -> dict:
    """
    Espera activamente hasta que el job finalice o falle.
    Retorna el resultado final con rutas de imagenes si disponibles.
    timeout: segundos maximos de espera (default 10 min para CPU)
    """
    elapsed = 0
    while elapsed < timeout:
        result = _query_job(job_id)
        stage = result.get("job_stage", "unknown")
        if stage in ("SUCCESS", "FAILED", "finished", "failed"):
            return result
        time.sleep(poll_interval)
        elapsed += poll_interval
    return {"job_stage": "timeout", "job_progress": 0, "error": "Timeout esperando generacion"}


def _query_job(job_id: str) -> dict:
    """Consulta puntual del estado de un job en Fooocus."""
    payload = json.dumps({"job_id": job_id, "require_step_preview": False}).encode()
    try:
        req = urllib.request.Request(
            f"{FOOOCUS_BASE_URL}/v1/generation/query-job",
            data=payload,
            headers={"Content-Type": "application/json"}
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"job_stage": "unknown", "job_progress": 0, "error": str(e)}


def get_latest_outputs(n: int = 10) -> list:
    """
    Devuelve las ultimas N imagenes generadas por Fooocus (por fecha de modificacion).
    Busca en el directorio outputs/ de Fooocus.
    """
    import glob as _glob
    images = []
    if not os.path.isdir(OUTPUT_DIR):
        return images
    for ext in ("*.png", "*.jpg", "*.jpeg", "*.webp"):
        images.extend(_glob.glob(os.path.join(OUTPUT_DIR, "**", ext), recursive=True))
    images.sort(key=os.path.getmtime, reverse=True)
    return images[:n]


# ─── Prompt Variation Generator ───────────────────────────────────────────────

SHOT_TYPES: list = [
    "A close-up shot", "A medium shot", "A wide shot", "A full body shot",
    "An extreme close-up shot", "A low angle shot", "A high angle shot",
    "An over-the-shoulder shot", "A Dutch angle shot", "A bird's eye view shot"
]


def generate_prompt_variations(
    base_prompt: str,
    shot_part: str = "A medium shot",
    activity_part: str = "captured in a modern studio",
    variations: int = 10,
) -> list:

    activities: list = [
        "captured in a Barcelona balcony drinking coffee",
        "studying for an exam at a university library",
        "finishing a tennis match on a clay court",
        "cooking in a modern kitchen",
        "walking through a busy city street at golden hour",
        "reading a book in a cozy cafe",
        "working on a laptop at a rooftop terrace",
        "taking selfies in a vintage clothing store",
        "jogging in a city park at sunrise",
        "attending a music festival in the crowd",
    ]

    count: int = min(variations, len(SHOT_TYPES), len(activities))
    prompts: list = []

    for i in range(count):
        shot: str     = SHOT_TYPES[i]
        activity: str = activities[i]
        if "[SHOT]" in base_prompt and "[ACTIVITY]" in base_prompt:
            varied: str = base_prompt.replace("[SHOT]", shot).replace("[ACTIVITY]", activity)
        else:
            varied = base_prompt.replace(shot_part, shot).replace(activity_part, activity)
        prompts.append(varied)

    return prompts


# ─── Batch Generation ─────────────────────────────────────────────────────────

def batch_generate(
    base_prompt: str,
    count: int = 5,
    reference_image_path: object = None,
) -> list:

    variations: list = generate_prompt_variations(base_prompt, variations=count)
    results: list = []

    for variant_prompt in variations:
        req_data: ImageGenRequest = {
            "prompt":              variant_prompt,
            "negative_prompt":     "ugly, deformed, blurry, low quality, watermark",
            "width":               832,
            "height":              1216,
            "num_images":          1,
            "performance":         "Speed",
            "style_selections":    ["Fooocus V2", "Fooocus Enhance"],
            "reference_image_path": reference_image_path,
        }
        result: ImageGenResponse = generate_image(req_data)
        results.append(result)

    return results


# ─── Self-test ────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("[Gravity :: Fooocus Client V9.3.1] Health check...")
    status: HealthStatus = health_check()
    print(f"  Online : {status['online']}")
    print(f"  Version: {status['version']}")
    print(f"  Message: {status['message']}")
    if status["online"]:
        print("\n  Ultimas imagenes generadas:")
        imgs = get_latest_outputs(5)
        if imgs:
            for p in imgs:
                print(f"    {p}")
        else:
            print("    (ninguna aun)")
