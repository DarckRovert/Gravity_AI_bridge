"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY AI — AI SCENE GENERATOR V1.0                                       ║
║  Genera fondos cinematográficos reales para cada sección de la canción      ║
║                                                                              ║
║  Cadena de prioridad:                                                        ║
║    1. Fooocus local (si está corriendo en :7865)                            ║
║    2. Pollinations API (modelo Flux, sin GPU local requerida)               ║
║    3. Fallback: gradiente procedural en numpy (sin dependencias externas)   ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import socket
import time
import urllib.request
import urllib.parse
import numpy as np
from core.logger import log


# ── Directorios ─────────────────────────────────────────────────────────────

_BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SCENE_CACHE_DIR = os.path.join(_BASE, "_videos", "_scene_cache")
os.makedirs(SCENE_CACHE_DIR, exist_ok=True)


# ── Mapeo engine → contexto visual ──────────────────────────────────────────

ENGINE_VISUAL_CONTEXT = {
    "space_odyssey": {
        "scene": "breathtaking cosmic void, lone figure silhouette standing on vast alien landscape at golden twilight",
        "style": "shot on 70mm Panavision anamorphic lens, IMAX format, epic cinematic landscape, volumetric raytraced lighting, photorealistic, Terrence Malick cinematography, unreal engine 5 lumen render, desolation and beauty, extreme wide angle, 8k resolution, masterpiece",
    },
    "nebula": {
        "scene": "floating deep inside the heart of a glowing cosmic nebula, divine celestial light filtering through stardust",
        "style": "mystical space art, hyper-photorealistic astrophotography, volumetric god rays, spiritual atmosphere, 8K ultra HD, deep space observatory, IMAX, breathtaking masterpiece",
    },
    "julia_fractal": {
        "scene": "colossal labyrinthine cathedral of glowing crystalline fractal geometry dissolving into infinite darkness",
        "style": "surreal mathematical architecture, hyper-detailed raytraced render, unreal engine 5, M.C. Escher meets cyberpunk, electric neon veins, cinematic lighting, 8k resolution, award-winning CGI",
    },
    "mandelbulb": {
        "scene": "deep inside a colossal alien biopunk megastructure of recursive impossible organic architecture",
        "style": "H.R. Giger meets Zaha Hadid, dark sci-fi masterpiece, photorealistic texturing, overwhelming scale, dramatic high-contrast lighting, 70mm anamorphic lens, unreal engine 5, ultra-detailed",
    },
    "quantum_tunnel": {
        "scene": "extreme velocity wormhole tunnel shattering the fabric of reality, pure chaotic light trails and motion blur",
        "style": "cinematic hyper-speed tunnel, photorealistic abstract light speed, explosive neon energy, Doctor Strange portal VFX style, IMAX cinematic motion, 8k resolution, raytraced reflections",
    },
}


# ── Constructores de prompt ──────────────────────────────────────────────────

def _build_prompt(engine: str, section_label: str, section_text: str,
                  color_hint: list = None) -> str:
    """
    Construye un prompt cinematográfico denso a partir del engine elegido
    por el AI Director y el contenido emocional de la sección de letra.
    """
    ctx = ENGINE_VISUAL_CONTEXT.get(engine, ENGINE_VISUAL_CONTEXT["space_odyssey"])
    scene = ctx["scene"]
    style = ctx["style"]

    # Color hint: si el AI Director devolvió colores, los traducimos a mood
    color_mood = ""
    if color_hint and len(color_hint) == 3:
        r, g, b = color_hint
        if b > max(r, g) + 0.15:
            color_mood = "cold blue atmosphere, indigo shadows,"
        elif r > max(g, b) + 0.15:
            color_mood = "warm crimson light, fiery orange glows,"
        elif g > max(r, b) + 0.1:
            color_mood = "emerald bioluminescence, teal atmosphere,"
        else:
            color_mood = "golden hour warm light, amber atmosphere,"

    prompt = f"{scene}, {color_mood} {style}, masterpiece, award-winning photography, ultra-detailed, no text, no watermark, no logo"
    log.info(f"[AISceneGen] '{section_label}' ({engine}): prompt generado ({len(prompt)} chars)")
    return prompt


# ── Backends de generación ───────────────────────────────────────────────────

def _fooocus_online() -> bool:
    """Verifica si Fooocus está activo en :7865."""
    try:
        s = socket.create_connection(("127.0.0.1", 7865), timeout=1.5)
        s.close()
        return True
    except:
        return False


def _generate_via_fooocus(prompt: str, w: int, h: int, out_path: str) -> bool:
    """
    Genera una imagen usando Fooocus local.
    Requiere que Fooocus esté corriendo con --listen.
    """
    try:
        import sys
        tools_dir = os.path.join(_BASE, "tools")
        if tools_dir not in sys.path:
            sys.path.insert(0, tools_dir)
        from fooocus_client import generate_image, ImageGenRequest

        req = {
            "prompt": prompt,
            "performance": "Quality",
            "width": w,
            "height": h,
            "num_images": 1,
        }
        result = generate_image(req)
        if result.get("success") and result.get("images"):
            import shutil
            shutil.copy2(result["images"][0], out_path)
            return True
    except Exception as e:
        log.warning(f"[AISceneGen] Fooocus error: {e}")
    return False


def _generate_via_pollinations(prompt: str, w: int, h: int, out_path: str,
                                seed: int = None, retries: int = 3) -> bool:
    """
    Genera una imagen usando la API pública de Pollinations (modelo Flux).
    # Flux: generar en 1024x576 y escalar — mejor calidad base para IBL
    gen_w, gen_h = 1024, 576
    # Modelos en orden de preferencia: flux-realism > flux > turbo
    MODELS = ["flux-realism", "flux", "turbo"]
    encoded = urllib.parse.quote(prompt[:480])  # URL seguro
    seed_str = f"&seed={seed}" if seed is not None else ""

    for attempt in range(retries):
        model = MODELS[attempt % len(MODELS)]
        timeout = 90 + attempt * 60  # 90s, 150s, 210s
        url = (
            f"https://image.pollinations.ai/prompt/{encoded}"
            f"?width={gen_w}&height={gen_h}&nologo=true&model={model}{seed_str}"
        )
        headers = {"User-Agent": "Mozilla/5.0 GravityAI/2.0"}
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                data = resp.read()
                if len(data) > 50000:  # Imagen real (>50KB)
                    try:
                        from PIL import Image
                        import io
                        img = Image.open(io.BytesIO(data))
                        if img.size != (w, h):
                            img = img.resize((w, h), Image.LANCZOS)
                        img.save(out_path, quality=95)
                    except ImportError:
                        with open(out_path, "wb") as f:
                            f.write(data)
                    log.info(f"[AISceneGen] Pollinations OK ({model}): {len(data)//1024}KB → {os.path.basename(out_path)} ({w}x{h})")
                    return True
                else:
                    log.warning(f"[AISceneGen] Pollinations respuesta pequeña ({len(data)}b) con modelo={model}, reintento {attempt+1}/{retries}")
        except Exception as e:
            log.warning(f"[AISceneGen] Pollinations intento {attempt+1}/{retries} (model={model}) error: {type(e).__name__}: {e}")
        if attempt < retries - 1:
            time.sleep(3 + attempt * 3)
    return False



def _generate_procedural_fallback(color1: list, color2: list, w: int, h: int,
                                   out_path: str) -> bool:
    """
    Fallback: genera una nebulosa cósmica procedural con ruido fractal.
    Sin dependencias de red. Siempre funciona y produce resultados hermosos.
    """
    try:
        from PIL import Image
        c1 = np.array(color1, dtype=np.float32)
        c2 = np.array(color2, dtype=np.float32)
        rng = np.random.RandomState(hash(out_path) % (2**32))

        # --- Ruido fractal multi-octava (FBM simulado) ---
        def fbm_noise(h_res, w_res, octaves=5, seed_offset=0):
            result = np.zeros((h_res, w_res), dtype=np.float32)
            amp = 0.5
            for o in range(octaves):
                freq = 2 ** o
                scale_h = max(1, h_res // freq)
                scale_w = max(1, w_res // freq)
                noise_small = rng.rand(scale_h, scale_w).astype(np.float32)
                # Resize nearest neighbour rápido
                noise_up = np.repeat(np.repeat(noise_small,
                    (h_res + scale_h - 1) // scale_h, axis=0),
                    (w_res + scale_w - 1) // scale_w, axis=1)[:h_res, :w_res]
                result += noise_up * amp
                amp *= 0.5
            return result / result.max()

        # --- Base: nebulosa de color con FBM ---
        nebula = fbm_noise(h, w, octaves=6)

        img = np.zeros((h, w, 3), dtype=np.float32)
        for i in range(3):
            img[:, :, i] = c1[i] * (1.0 - nebula) + c2[i] * nebula

        # --- Segundo manto de nebulosa desplazado para profundidad ---
        nebula2 = fbm_noise(h, w, octaves=4)
        c_accent = np.clip(c1 * 0.3 + np.array([0.05, 0.02, 0.15], dtype=np.float32), 0, 1)
        for i in range(3):
            img[:, :, i] += c_accent[i] * nebula2 * 0.4

        # --- Estrellas: puntos aleatorios brillantes ---
        n_stars = int(w * h * 0.001)  # 0.1% de píxeles
        sy = rng.randint(0, h, n_stars)
        sx = rng.randint(0, w, n_stars)
        brightness = rng.uniform(0.4, 1.0, n_stars).astype(np.float32)
        for i in range(3):
            img[sy, sx, i] = np.clip(img[sy, sx, i] + brightness, 0, 1)

        # --- Viñeta cinematográfica profunda ---
        yy, xx = np.mgrid[0:h, 0:w]
        cx, cy = w / 2, h / 2
        dist = np.sqrt(((xx - cx) / (w * 0.55)) ** 2 + ((yy - cy) / (h * 0.55)) ** 2)
        vignette = 1.0 - np.clip(dist * 1.2, 0, 0.92)
        for i in range(3):
            img[:, :, i] *= vignette

        img = np.clip(img * 255, 0, 255).astype(np.uint8)
        Image.fromarray(img).save(out_path, quality=95)
        log.info(f"[AISceneGen] Fallback procedural (nebulosa cosmica) guardado: {os.path.basename(out_path)}")
        return True
    except Exception as e:
        log.error(f"[AISceneGen] Fallback procedural error: {e}")
        return False



# ── API Pública ──────────────────────────────────────────────────────────────

def generate_scene_images(timeline: list, w: int = 1280, h: int = 720,
                           colorsA: np.ndarray = None,
                           force_pollinations: bool = False) -> list:
    """
    Genera una imagen de fondo cinematográfica por cada escena del timeline.

    Args:
        timeline:          Lista de dicts {start, end, engine, pose}.
        w, h:              Resolución objetivo.
        colorsA:           Array numpy (total_frames, 3) de colores del AI Director.
        force_pollinations: Si True, ignora Fooocus aunque esté disponible.

    Returns:
        Lista de rutas absolutas a imágenes PNG/JPG, una por entrada en timeline.
        Si falla una escena, usa la anterior o el fallback procedural.
    """
    use_fooocus = (not force_pollinations) and _fooocus_online()
    backend = "Fooocus" if use_fooocus else "Pollinations"
    log.info(f"[AISceneGen] Backend seleccionado: {backend} — {len(timeline)} escenas")

    scene_images = []
    last_valid_path = None

    for i, scene in enumerate(timeline):
        engine = scene.get("engine", "space_odyssey")
        label = f"escena_{i+1}_{engine}"
        cache_key = f"{label}_{w}x{h}.jpg"
        out_path = os.path.join(SCENE_CACHE_DIR, cache_key)

        # Usar caché si existe (evita regenerar en re-renders)
        if os.path.isfile(out_path) and os.path.getsize(out_path) > 10000:
            log.info(f"[AISceneGen] Cache hit: {cache_key}")
            scene_images.append(out_path)
            last_valid_path = out_path
            continue

        # Extraer color hint de colorsA (frame del centro de la escena)
        color_hint = None
        if colorsA is not None and len(colorsA) > 0:
            mid_frame = (scene["start"] + scene["end"]) // 2
            mid_frame = min(mid_frame, len(colorsA) - 1)
            color_hint = colorsA[mid_frame].tolist()

        prompt = _build_prompt(
            engine=engine,
            section_label=label,
            section_text=scene.get("label", ""),
            color_hint=color_hint,
        )

        success = False
        if use_fooocus:
            success = _generate_via_fooocus(prompt, w, h, out_path)

        if not success:
            success = _generate_via_pollinations(prompt, w, h, out_path, seed=i * 137)

        if not success:
            log.warning(f"[AISceneGen] Usando fallback procedural para escena {i+1}")
            c1 = color_hint or [0.05, 0.02, 0.15]
            c2 = [c * 0.3 for c in c1]
            success = _generate_procedural_fallback(c1, c2, w, h, out_path)

        if success:
            scene_images.append(out_path)
            last_valid_path = out_path
        elif last_valid_path:
            log.warning(f"[AISceneGen] Escena {i+1} fallida, reutilizando imagen anterior")
            scene_images.append(last_valid_path)
        else:
            scene_images.append(None)

    log.info(f"[AISceneGen] {sum(1 for p in scene_images if p)} / {len(timeline)} imágenes generadas")
    return scene_images
