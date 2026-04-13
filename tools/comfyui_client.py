"""
Gravity AI Bridge v9.0 PRO — ComfyUI (ZLUDA) Satellite Client
Tool: comfyui_client
Endpoint: http://127.0.0.1:8188 (ComfyUI API mode)
Hardware: AMD Ryzen 7 8700G, Radeon 780M iGPU, 16GB UMA VRAM
"""

import os
import json
import random
import urllib.request
import urllib.error
from typing import TypedDict, Literal, Any


# ─── Constants ────────────────────────────────────────────────────────────────

COMFYUI_BASE_URL: str = os.getenv("COMFYUI_URL", "http://127.0.0.1:8188")
OUTPUT_DIR: str = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "_integrations", "ComfyUI-Zluda", "output")
)

SHOT_TYPES: list[str] = [
    "A close-up shot", "A medium shot", "A wide shot", "A full body shot",
    "An extreme close-up shot", "A low angle shot", "A high angle shot",
    "An over-the-shoulder shot", "A Dutch angle shot", "A bird's eye view shot"
]

# ─── TypedDicts ───────────────────────────────────────────────────────────────

class ImageGenRequest(TypedDict, total=False):
    prompt: str
    negative_prompt: str
    width: int
    height: int
    num_images: int
    performance: Literal["Speed", "Quality", "Extreme Speed"]
    style_selections: list[str]
    reference_image_path: str | None


class ImageGenResponse(TypedDict):
    success: bool
    images: list[str]
    error: str | None
    job_id: str | None


class HealthStatus(TypedDict):
    online: bool
    version: str | None
    message: str


# ─── Health Check ─────────────────────────────────────────────────────────────

def health_check() -> HealthStatus:
    try:
        req = urllib.request.Request(f"{COMFYUI_BASE_URL}/system_stats")
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                return {
                    "online": True,
                    "version": "ComfyUI (ZLUDA)",
                    "message": "ComfyUI Satellite API is responsive."
                }
    except Exception as e:
        return {
            "online": False,
            "version": None,
            "message": f"ComfyUI offline. Launch ComfyUI ZLUDA environment. Error: {e}"
        }
    return {"online": False, "version": None, "message": "Unknown HTTP Error"}


# ─── Image Generation ─────────────────────────────────────────────────────────

def generate_image(request: ImageGenRequest) -> ImageGenResponse:
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    prompt_text: str = request.get("prompt", "")
    neg_prompt: str = request.get("negative_prompt", "")
    width: int = request.get("width", 1024)
    height: int = request.get("height", 1024)
    batch: int = request.get("num_images", 1)

    # ComfyUI base SDXL Workflow Payload
    workflow: dict[str, Any] = {
        "3": {
            "inputs": {
                "seed": random.randint(1, 99999999999), 
                "steps": 30, 
                "cfg": 7, 
                "sampler_name": "dpmpp_2m", 
                "scheduler": "karras", 
                "denoise": 1, 
                "model": ["4", 0], 
                "positive": ["6", 0], 
                "negative": ["7", 0], 
                "latent_image": ["5", 0]
            }, 
            "class_type": "KSampler"
        },
        "4": {"inputs": {"ckpt_name": "juggernautXL_v8Rundiffusion.safetensors"}, "class_type": "CheckpointLoaderSimple"},
        "5": {"inputs": {"width": width, "height": height, "batch_size": batch}, "class_type": "EmptyLatentImage"},
        "6": {"inputs": {"text": prompt_text, "clip": ["4", 1]}, "class_type": "CLIPTextEncode"},
        "7": {"inputs": {"text": neg_prompt, "clip": ["4", 1]}, "class_type": "CLIPTextEncode"},
        "8": {"inputs": {"samples": ["3", 0], "vae": ["4", 2]}, "class_type": "VAEDecode"},
        "9": {"inputs": {"filename_prefix": "Gravity_Gen", "images": ["8", 0]}, "class_type": "SaveImage"}
    }

    payload_data = json.dumps({"prompt": workflow}).encode("utf-8")
    
    try:
        req = urllib.request.Request(
            f"{COMFYUI_BASE_URL}/prompt", 
            data=payload_data, 
            headers={'Content-Type': 'application/json'}
        )
        with urllib.request.urlopen(req, timeout=600) as response:
            res_data = json.loads(response.read())
            prompt_id: str | None = res_data.get("prompt_id")
            
            return {
                "success": True,
                "images": [], # ComfyUI writes directly to its local /output path asynchronously
                "error": None,
                "job_id": prompt_id
            }
    except Exception as e:
        return {
            "success": False,
            "images": [],
            "error": f"API Error: {e}",
            "job_id": None
        }


# ─── Prompt Variation Generator ───────────────────────────────────────────────

def generate_prompt_variations(
    base_prompt: str,
    shot_part: str = "A medium shot",
    activity_part: str = "captured in a modern studio",
    variations: int = 10,
) -> list[str]:
    
    activities: list[str] = [
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
    prompts: list[str] = []

    for i in range(count):
        shot: str = SHOT_TYPES[i]
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
    reference_image_path: str | None = None,
) -> list[ImageGenResponse]:
    
    variations: list[str] = generate_prompt_variations(base_prompt, variations=count)
    results: list[ImageGenResponse] = []

    for variant_prompt in variations:
        req: ImageGenRequest = {
            "prompt": variant_prompt,
            "negative_prompt": "",
            "width": 1024,
            "height": 1024,
            "num_images": 1,
            "performance": "Speed",
            "style_selections": [],
            "reference_image_path": reference_image_path,
        }
        result: ImageGenResponse = generate_image(req)
        results.append(result)

    return results


if __name__ == "__main__":
    print("[Gravity :: ComfyUI Client] Health check...")
    status: HealthStatus = health_check()
    print(f"  Online : {status['online']}")
    print(f"  Version: {status['version']}")
    print(f"  Message: {status['message']}")
