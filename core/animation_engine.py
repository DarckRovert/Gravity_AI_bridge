"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY AI — ANIMATION ENGINE V1.0                                         ║
║  Motor de Animación de Imágenes (MAI) — Gravity Studio V15.1 PRO               ║
║                                                                              ║
║  Sistema de 3 niveles con fallback progresivo:                              ║
║    L0 — FFmpeg nativo (zoompan, filtros básicos) — sin dependencias         ║
║    L1 — Procedural avanzado (parallax, glitch, pulse, etc.) — sin deps      ║
║    L2 — AnimateDiff/ComfyUI (IA local) — requiere ComfyUI online            ║
║                                                                              ║
║  Integración:                                                                ║
║    from core.animation_engine import build_animation_vf, resolve_effect     ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import math
import subprocess
from typing import Optional

# ── Catálogo de efectos disponibles ──────────────────────────────────────────
ANIMATION_EFFECTS: dict[str, str] = {
    "kenburns":       "Ken Burns (Zoom + Pan Extendido)",
    "parallax":       "Parallax Simulado (Capas de Profundidad)",
    "pulse":          "Respiración / Pulse (Zoom Orgánico)",
    "glitch":         "Glitch Cinematográfico (RGB Shift)",
    "vignette_drift": "Deriva con Viñeta (Pan Lento)",
    "film_burn":      "Quemado de Película (Analógico)",
    "tilt_shift":     "Tilt-Shift Blur (Profundidad de Campo)",
    "shake":          "Temblor de Cámara (Handheld)",
    "none":           "Sin animación (Imagen estática)",
}

# ── Mapeo automático estilo cinematográfico → efecto de animación ─────────────
ANIMATION_DEFAULTS: dict[str, str] = {
    "documental":   "kenburns",
    "anime":        "pulse",
    "epico":        "kenburns",
    "noir":         "vignette_drift",
    "infantil":     "pulse",
    "naturaleza":   "kenburns",
    "cyberpunk":    "glitch",
    "historico":    "film_burn",
    "lofi":         "pulse",
    "retro80s":     "glitch",
    "publicitario": "shake",
    "cinematic":    "vignette_drift",
}

# ── Variantes de Ken Burns (6 modos cinemáticos) ─────────────────────────────
_KB_VARIANTS = [
    # 0: Zoom-in suave centrado
    lambda total_frames, w, h: (
        "min(zoom+0.0008,1.20)",
        "iw/2-(iw/zoom/2)",
        "ih/2-(ih/zoom/2)"
    ),
    # 1: Zoom-out con pan derecha
    lambda total_frames, w, h: (
        f"if(eq(on,1),1.20,max(zoom-0.0007,1.0))",
        f"iw/2-(iw/zoom/2)+(iw*0.04*on/{total_frames})",
        "ih/2-(ih/zoom/2)"
    ),
    # 2: Zoom-in con pan izquierda
    lambda total_frames, w, h: (
        "min(zoom+0.0007,1.18)",
        f"iw/2-(iw/zoom/2)-(iw*0.03*on/{total_frames})",
        "ih/2-(ih/zoom/2)"
    ),
    # 3: Zoom-out con pan arriba-derecha (diagonal)
    lambda total_frames, w, h: (
        f"if(eq(on,1),1.18,max(zoom-0.0006,1.0))",
        f"iw/2-(iw/zoom/2)+(iw*0.025*on/{total_frames})",
        f"ih/2-(ih/zoom/2)-(ih*0.02*on/{total_frames})"
    ),
    # 4: Zoom-in con pan abajo-izquierda
    lambda total_frames, w, h: (
        "min(zoom+0.0006,1.16)",
        f"iw/2-(iw/zoom/2)-(iw*0.02*on/{total_frames})",
        f"ih/2-(ih/zoom/2)+(ih*0.02*on/{total_frames})"
    ),
    # 5: Zoom estático con pan lento horizontal (dolly)
    lambda total_frames, w, h: (
        "1.08",
        f"iw*0.02*on/{total_frames}",
        "ih/2-(ih/zoom/2)"
    ),
]


def resolve_effect(style: str, animation_effect: str) -> str:
    """
    Resuelve el efecto de animación efectivo.
    Si animation_effect es 'auto', usa el default del estilo.
    Si animation_effect es un ID válido, lo usa directamente.
    Fallback a 'kenburns' si nada coincide.
    """
    if animation_effect == "auto" or animation_effect not in ANIMATION_EFFECTS:
        return ANIMATION_DEFAULTS.get(style, "kenburns")
    return animation_effect


def build_animation_vf(
    effect: str,
    clip_dur: float,
    fps: int,
    w: int,
    h: int,
    scene_idx: int,
) -> str:
    """
    Genera el string de filtro FFmpeg para el efecto de animación dado.

    Args:
        effect:     ID del efecto (de ANIMATION_EFFECTS).
        clip_dur:   Duración del clip en segundos.
        fps:        Frames por segundo del video de salida.
        w, h:       Resolución del clip.
        scene_idx:  Índice de escena (0-based), usado para variar efectos.

    Returns:
        String de filtro FFmpeg listo para usar en -vf.
        Nunca lanza excepción — fallback a kenburns si hay error interno.
    """
    try:
        total_frames = max(1, int(clip_dur * fps))

        if effect == "none":
            return f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,fps={fps}"

        elif effect == "kenburns":
            return _build_kenburns(total_frames, w, h, fps, scene_idx)

        elif effect == "pulse":
            return _build_pulse(total_frames, w, h, fps, clip_dur)

        elif effect == "vignette_drift":
            return _build_vignette_drift(total_frames, w, h, fps, scene_idx)

        elif effect == "glitch":
            return _build_glitch(total_frames, w, h, fps, clip_dur)

        elif effect == "film_burn":
            return _build_film_burn(total_frames, w, h, fps, clip_dur)

        elif effect == "shake":
            return _build_shake(total_frames, w, h, fps, scene_idx)

        elif effect == "tilt_shift":
            return _build_tilt_shift(w, h, fps)

        elif effect == "parallax":
            return _build_parallax(total_frames, w, h, fps, scene_idx)

        else:
            # Efecto desconocido → kenburns por defecto
            return _build_kenburns(total_frames, w, h, fps, scene_idx)

    except Exception:
        # Nunca fallar — fallback seguro
        return f"scale={w}:{h}:force_original_aspect_ratio=decrease,pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,fps={fps}"


# ── Implementaciones de cada efecto ──────────────────────────────────────────

def _build_kenburns(total_frames: int, w: int, h: int, fps: int, scene_idx: int) -> str:
    """
    Genera un filtro zoompan de FFmpeg para el efecto Ken Burns (Zoom + Pan).
    
    Args:
        total_frames: Cantidad total de frames del fragmento de video.
        w: Ancho de resolución objetivo.
        h: Alto de resolución objetivo.
        fps: Tasa de fotogramas por segundo.
        scene_idx: Índice numérico de la escena para variar el patrón.

    Returns:
        Cadena formateada con la cláusula zoompan para FFmpeg.
    """
    variant_fn = _KB_VARIANTS[scene_idx % len(_KB_VARIANTS)]
    z, x, y = variant_fn(total_frames, w, h)
    return (
        f"zoompan=z='{z}':d={total_frames}"
        f":x='{x}':y='{y}'"
        f":s={w}x{h}:fps={fps}"
    )


def _build_pulse(total_frames: int, w: int, h: int, fps: int, clip_dur: float) -> str:
    """
    Genera un filtro zoompan de respiración sinusoidal lenta (Zoom pulsante).
    
    Args:
        total_frames: Cantidad total de frames del fragmento de video.
        w: Ancho de resolución objetivo.
        h: Alto de resolución objetivo.
        fps: Tasa de fotogramas por segundo.
        clip_dur: Duración en segundos del clip.

    Returns:
        Cadena formateada con el zoompan oscilante.
    """
    period = min(clip_dur, 4.0)  # período en segundos
    frames_per_period = max(1, int(period * fps))
    zoom_expr = f"1.03+0.03*sin(2*PI*on/{frames_per_period})"
    return (
        f"zoompan=z='{zoom_expr}':d={total_frames}"
        f":x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)'"
        f":s={w}x{h}:fps={fps}"
    )


def _build_vignette_drift(total_frames: int, w: int, h: int, fps: int, scene_idx: int) -> str:
    """
    Genera una deriva sutil y lenta de cámara combinada con una viñeta dramática.
    
    Args:
        total_frames: Cantidad total de frames del fragmento de video.
        w: Ancho de resolución objetivo.
        h: Alto de resolución objetivo.
        fps: Tasa de fotogramas por segundo.
        scene_idx: Índice numérico de la escena para alternar la dirección.

    Returns:
        Filtro FFmpeg concatenado de zoompan y viñeta.
    """
    direction = 1 if scene_idx % 2 == 0 else -1
    # Pan de 3% del ancho a lo largo del clip
    pan_expr = f"iw/2-(iw/zoom/2)+({direction}*iw*0.03*on/{total_frames})"
    return (
        f"zoompan=z='1.05':d={total_frames}"
        f":x='{pan_expr}':y='ih/2-(ih/zoom/2)'"
        f":s={w}x{h}:fps={fps},"
        f"vignette=PI/4"
    )


def _build_glitch(total_frames: int, w: int, h: int, fps: int, clip_dur: float) -> str:
    """
    Genera un filtro de glitch analógico intermitente con RGB Shift y ruido digital.
    
    Args:
        total_frames: Cantidad total de frames del fragmento de video.
        w: Ancho de resolución objetivo.
        h: Alto de resolución objetivo.
        fps: Tasa de fotogramas por segundo.
        clip_dur: Duración total en segundos.

    Returns:
        Cadena de filtros encadenados (scale, pad, fps, rgbashift, noise).
    """
    return (
        f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
        f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,"
        f"fps={fps},"
        f"rgbashift=rh=2:bh=-2:rv=1:bv=-1,"
        f"noise=alls=4:allf=t"
    )


def _build_film_burn(total_frames: int, w: int, h: int, fps: int, clip_dur: float) -> str:
    """
    Simula una transición de quemado de película clásica con curvas vintage, grano y destellos.
    
    Args:
        total_frames: Cantidad total de frames del fragmento de video.
        w: Ancho de resolución objetivo.
        h: Alto de resolución objetivo.
        fps: Tasa de fotogramas por segundo.
        clip_dur: Duración en segundos.

    Returns:
        Cadena de filtros encadenados (vintage curves, noise, fade in blanco).
    """
    burn_frames = min(int(fps * 1.5), total_frames // 3)
    return (
        f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
        f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,"
        f"fps={fps},"
        f"curves=vintage,"
        f"noise=alls=8:allf=t+u,"
        f"fade=t=in:st=0:d={burn_frames/fps:.2f}:color=white"
    )


def _build_shake(total_frames: int, w: int, h: int, fps: int, scene_idx: int) -> str:
    """
    Produce un temblor de cámara simulado (estilo cámara en mano o handheld) con margen de re-encuadre.
    
    Args:
        total_frames: Cantidad total de frames del fragmento de video.
        w: Ancho de resolución objetivo.
        h: Alto de resolución objetivo.
        fps: Tasa de fotogramas por segundo.
        scene_idx: Índice numérico de la escena.

    Returns:
        Cadena de filtros de sobreescala, recorte dinámico y FPS.
    """
    shake_px = max(4, min(12, w // 100))  # 1% del ancho, mín 4px, máx 12px
    freq = 3.5  # Hz de vibración
    frames_per_cycle = max(1, int(fps / freq))
    # Pad para dar margen al shake
    pad = shake_px * 2
    x_expr = f"({shake_px}*sin(2*PI*n/{frames_per_cycle}))+{shake_px}"
    y_expr = f"({shake_px // 2}*cos(2*PI*n/{frames_per_cycle}))+{shake_px // 2}"
    return (
        f"scale={w + pad}:{h + pad}:force_original_aspect_ratio=increase,"
        f"crop={w}:{h}:'{x_expr}':'{y_expr}',"
        f"fps={fps}"
    )


def _build_tilt_shift(w: int, h: int, fps: int) -> str:
    """
    Simula el efecto óptico Tilt-Shift (profundidad de campo miniatura) mediante boxblur y viñeta.
    
    Args:
        w: Ancho de resolución objetivo.
        h: Alto de resolución objetivo.
        fps: Tasa de fotogramas por segundo.

    Returns:
        Cadena de filtros seguros y de compatibilidad universal.
    """
    return (
        f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
        f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,"
        f"fps={fps},"
        f"boxblur=luma_radius=2:luma_power=1,"
        f"vignette=PI/3.5"
    )


def _build_parallax(total_frames: int, w: int, h: int, fps: int, scene_idx: int) -> str:
    """
    Simula profundidad espacial parallax aumentando levemente la escala y desplazando en sentido opuesto.
    
    Args:
        total_frames: Cantidad total de frames del fragmento de video.
        w: Ancho de resolución objetivo.
        h: Alto de resolución objetivo.
        fps: Tasa de fotogramas por segundo.
        scene_idx: Índice numérico de la escena.

    Returns:
        Cadena de filtros de escala y recorte en movimiento.
    """
    direction = 1 if scene_idx % 2 == 0 else -1
    scale_factor = 1.25
    pan_pct = 0.08
    sw = int(w * scale_factor)
    sh = int(h * scale_factor)
    x_offset = (sw - w) // 2
    y_offset = (sh - h) // 2
    pan_px = int(sw * pan_pct)
    x_expr = f"{x_offset}+({direction}*{pan_px}*n/{total_frames})"
    return (
        f"scale={sw}:{sh}:force_original_aspect_ratio=increase,"
        f"crop={w}:{h}:'{x_expr}':{y_offset},"
        f"fps={fps}"
    )


# ── Motor L1.5: Multi-Variación via Pollinations + FFmpeg ────────────────────

def animate_with_variations(
    image_path: str,
    prompt: str,
    job_id: int,
    scene_idx: int,
    fps: int = 8,
    duration: float = 4.0,
    n_variations: int = 4,
    output_dir: str = "",
    ffmpeg_exe: str = "ffmpeg",
    target_w: int = 0,
    target_h: int = 0,
) -> Optional[str]:
    """
    Motor L1.5 — Genera N variaciones de la imagen via Pollinations y las interpola
    con crossfade cinematográfico + movimiento de cámara para crear la ilusión de video.

    Cada variación usa la misma descripción visual pero con seed diferente, produciendo
    cambios sutiles de iluminación, detalle y composición. FFmpeg los une con xfade
    disolviendo suavemente entre imágenes mientras aplica el efecto de movimiento activo.
    Args:
        image_path:   Ruta a la imagen base de la escena.
        prompt:       Prompt positivo para Pollinations (descripción visual de la escena).
        job_id:       ID del trabajo actual.
        scene_idx:    Índice de la escena (0-based).
        fps:          Frames por segundo del clip de salida.
        duration:     Duración total del clip en segundos.
        n_variations: Número de variaciones a generar (4-6 recomendado).
        output_dir:   Carpeta de salida; por defecto _videos/job_{job_id}/.
        ffmpeg_exe:   Ruta al ejecutable de FFmpeg.

    Returns:
        Ruta absoluta al clip MP4 generado, o None si falla.
    """
    import tempfile
    import shutil
    import urllib.request
    import urllib.parse
    import sys
    import os
    import subprocess
    from typing import Optional

    _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    if not output_dir:
        output_dir = os.path.join(_base, "_videos", f"job_{job_id}")
    os.makedirs(output_dir, exist_ok=True)

    if not os.path.isfile(ffmpeg_exe):
        ffmpeg_exe = os.path.join(_base, "_integrations", "ffmpeg", "ffmpeg.exe")
        if not os.path.isfile(ffmpeg_exe):
            ffmpeg_exe = "ffmpeg"

    # Validar imagen base y calcular dimensiones de trabajo
    try:
        from PIL import Image as _PIL_check
        with _PIL_check.open(image_path) as _img:
            img_w, img_h = _img.size
    except Exception:
        img_w, img_h = 1280, 720

    # Usar resolución objetivo si se especificó, si no usar tamaño real de la imagen
    if target_w > 0 and target_h > 0:
        w = target_w if target_w % 2 == 0 else target_w - 1
        h = target_h if target_h % 2 == 0 else target_h - 1
    else:
        w = img_w if img_w % 2 == 0 else img_w - 1
        h = img_h if img_h % 2 == 0 else img_h - 1

     # ── Generador local de variaciones (sin peticiones de red) ─────────────────
    # Las variaciones se generan mediante transformaciones geométricas y de color
    # aplicadas localmente sobre la imagen base. Sin API, sin bans, sin latencia.
    # Tipos de transformación cinematográfica por variación:
    _LOCAL_TRANSFORMS = [
        {"zoom": 1.00, "pan_x": 0,     "pan_y": 0,     "brightness": 1.00},  # var0: original
        {"zoom": 1.04, "pan_x": 0,     "pan_y": 0,     "brightness": 1.00},  # var1: zoom-in suave
        {"zoom": 1.04, "pan_x": +0.03, "pan_y": 0,     "brightness": 1.02},  # var2: zoom + pan derecha + brillo
        {"zoom": 1.07, "pan_x": +0.03, "pan_y": -0.02, "brightness": 1.02},  # var3: zoom mayor + pan diagonal
    ]

    variation_paths: list[str] = []

    try:
        from PIL import Image, ImageEnhance
    except Exception as _pil_err:
        from core.logger import log
        log.warning(f"[VideoStudio] PIL no disponible para variaciones locales: {_pil_err}")
        return None

    with Image.open(image_path) as _base_img:
        base_pil = _base_img.convert("RGB")
        bw, bh = base_pil.size

    for i in range(n_variations):
        var_path = os.path.join(output_dir, f"scene_{scene_idx:02d}_var{i:02d}.png")
        t = _LOCAL_TRANSFORMS[i % len(_LOCAL_TRANSFORMS)]
        try:
            img = base_pil.copy()

            # Aplicar zoom + pan como recorte centrado con offset
            zoom = t["zoom"]
            crop_w = int(bw / zoom)
            crop_h = int(bh / zoom)
            # Pan: desplazamiento porcentual del centro
            offset_x = int(bw * t["pan_x"])
            offset_y = int(bh * t["pan_y"])
            cx = bw // 2 + offset_x
            cy = bh // 2 + offset_y
            left  = max(0, cx - crop_w // 2)
            top   = max(0, cy - crop_h // 2)
            right = min(bw, left + crop_w)
            bot   = min(bh, top + crop_h)
            img = img.crop((left, top, right, bot)).resize((bw, bh), Image.Resampling.LANCZOS)

            # Ajuste de brillo sutil
            if t["brightness"] != 1.0:
                img = ImageEnhance.Brightness(img).enhance(t["brightness"])

            # Redimensionar a la resolución objetivo si es necesario
            if (bw, bh) != (w, h):
                img = img.resize((w, h), Image.Resampling.LANCZOS)

            img.save(var_path, "PNG")
            variation_paths.append(var_path)
        except Exception as _ve:
            from core.logger import log
            log.warning(f"[VideoStudio] Error en variación local {i}: {_ve}. Usando copia directa.")
            shutil.copy2(image_path, var_path)
            variation_paths.append(var_path)

    # ── Bonus: 1 variación Pollinations si la API no está bloqueada ─────────────
    # Solo se intenta si tenemos cuota disponible — no bloquea el pipeline si falla.
    try:
        from tools.pollinations_generator import generate as poll_gen, is_blocked
        if not is_blocked():
            bonus_path = os.path.join(output_dir, f"scene_{scene_idx:02d}_var_bonus.png")
            bonus_prompt = f"{prompt.strip().replace(chr(10), ' ')[:180]}. Cinematic still, slight different angle."
            bonus_seed = (job_id * 1000 + scene_idx * 7 + 99) % (2**31)
            result = poll_gen(
                prompt=bonus_prompt, output_path=bonus_path,
                width=w, height=h, model="flux",
                seed=bonus_seed, enhance=False, nologo=True,
            )
            if result.get("success") and os.path.isfile(bonus_path):
                variation_paths.append(bonus_path)
                from core.logger import log
                log.info(f"[VideoStudio] [L1.5] Escena {scene_idx}: variación bonus Pollinations añadida.")
    except Exception:
        pass  # Bonus es opcional, fallo silencioso

    if len(variation_paths) < 2:
        # No hay suficientes variaciones — devolver None para que el pipeline use L1
        return None

    # Construir clip con FFmpeg usando xfade entre variaciones
    # Duración de cada segmento y overlap para crossfade
    n = len(variation_paths)
    seg_dur = duration / n
    xfade_dur = min(0.5, seg_dur * 0.3)  # 30% de overlap, máx 0.5s
    effect_idx = scene_idx % len(_KB_VARIANTS)

    # Construir filtergraph xfade en cadena
    # Cada imagen se convierte a un loop de seg_dur segundos con su efecto de movimiento
    total_frames_per_seg = max(1, int(seg_dur * fps))

    input_args: list[str] = []
    filter_parts: list[str] = []
    last_label = "[v0]"

    for idx, vpath in enumerate(variation_paths):
        input_args += ["-loop", "1", "-t", f"{seg_dur:.3f}", "-i", vpath]
        z, x, y = _KB_VARIANTS[(effect_idx + idx) % len(_KB_VARIANTS)](total_frames_per_seg, w, h)
        kbf = (
            f"scale={w}:{h}:force_original_aspect_ratio=increase,"
            f"crop={w}:{h},"
            f"zoompan=z='{z}':d={total_frames_per_seg}:x='{x}':y='{y}':s={w}x{h}:fps={fps},"
            f"setpts=PTS-STARTPTS"
        )
        filter_parts.append(f"[{idx}:v]{kbf}[seg{idx}]")

    # Encadenar xfades
    offset = seg_dur - xfade_dur
    xfade_filters: list[str] = []
    prev_label = "[seg0]"
    for idx in range(1, n):
        out_label = f"[xf{idx}]" if idx < n - 1 else "[vout]"
        xfade_filters.append(
            f"{prev_label}[seg{idx}]xfade=transition=fade:duration={xfade_dur:.3f}:offset={offset:.3f}{out_label}"
        )
        offset += seg_dur - xfade_dur
        prev_label = f"[xf{idx}]"

    full_filter = ";".join(filter_parts + xfade_filters)

    out_path = os.path.join(output_dir, f"scene_{scene_idx:02d}_anim_l15.mp4")

    cmd = (
        [ffmpeg_exe, "-y"]
        + input_args
        + [
            "-filter_complex", full_filter,
            "-map", "[vout]",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-color_range", "tv",
            "-colorspace", "bt709",
            "-color_trc", "bt709",
            "-color_primaries", "bt709",
            "-movflags", "+faststart",
            "-t", f"{duration:.3f}",
            out_path,
        ]
    )

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        if result.returncode == 0 and os.path.isfile(out_path) and os.path.getsize(out_path) > 1000:
            return out_path
    except Exception:
        pass

    return None


# ── Motor L2: ComfyUI / AnimateDiff ──────────────────────────────────────────

def animate_with_comfyui(
    image_path: str,
    job_id: int,
    scene_idx: int,
    fps: int = 8,
    frames: int = 8,
    output_dir: str = "",
) -> Optional[str]:
    """
    Genera un clip MP4 animado a partir de una imagen estática usando ComfyUI (Image-to-Video).
    Utiliza el ConfigManager global para un acceso seguro y concurrente a la configuración.
    
    Args:
        image_path: Ruta a la imagen fuente en disco.
        job_id: Identificador único del trabajo de renderización.
        scene_idx: Índice relativo de la escena.
        fps: Tasa de fotogramas por segundo a renderizar.
        frames: Cantidad total de fotogramas a animar.
        output_dir: Directorio de salida opcional.

    Returns:
        Ruta absoluta al archivo de video generado (.mp4), o None si falla.
    """
    if not image_path or not os.path.isfile(image_path):
        return None

    try:
        import sys as _sys
        _base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        _int_dir = os.path.join(_base, "_integrations")
        if _int_dir not in _sys.path:
            _sys.path.insert(0, _int_dir)

        from comfy_client import ComfyUIClient
        
        host, port = "127.0.0.1", 8188
        try:
            # Consumo thread-safe y centralizado mediante el ConfigManager global
            from core.config_manager import config as _sys_config
            _c_url = _sys_config.get("comfyui.url", "http://127.0.0.1:8188")
            if "://" in _c_url:
                _c_url = _c_url.split("://")[1]
            if ":" in _c_url:
                host, port_str = _c_url.split(":")
                port = int(port_str)
            else:
                host = _c_url
        except Exception:
            pass

        client = ComfyUIClient(host=host, port=port)

        if not client.is_online():
            comfy_dir = os.path.join(_int_dir, "ComfyUI_windows_portable")
            bat_file = os.path.join(comfy_dir, "run_amd_gpu.bat")
            if os.path.exists(bat_file):
                import subprocess
                import time
                try:
                    from core.logger import log
                    log.info("[Animation Engine] ComfyUI offline. Auto-Starting run_amd_gpu.bat...")
                    CREATE_NEW_CONSOLE = getattr(subprocess, "CREATE_NEW_CONSOLE", 0x00000010)
                    subprocess.Popen([bat_file], cwd=comfy_dir, creationflags=CREATE_NEW_CONSOLE, shell=True)
                    for _ in range(30):
                        time.sleep(2.0)
                        if client.is_online():
                            log.info("[Animation Engine] ComfyUI started successfully.")
                            break
                except Exception as e:
                    pass

        if not client.is_online():
            return None

        # Determinar resolución desde la imagen
        w, h = 512, 512
        try:
            from PIL import Image
            with Image.open(image_path) as img:
                w, h = img.size
                # Reducir para ComfyUI (cost computacional)
                if w > 512:
                    scale = 512 / w
                    w = 512
                    h = int(h * scale)
                    h = h - (h % 8)  # múltiplo de 8
                    w = w - (w % 8)
        except Exception:
            pass

        # Subir la imagen al servidor ComfyUI (LoadImage requiere nombre relativo, no ruta absoluta)
        try:
            uploaded_name = client.upload_image(image_path)
        except Exception as _ue:
            try:
                from core.logger import log
                log.warning(f"[Animation Engine] upload_image falló: {_ue}. Usando nombre base.")
            except Exception:
                pass
            uploaded_name = os.path.basename(image_path)

        workflow = client.build_img2video_workflow(
            image_path=uploaded_name,
            width=w,
            height=h,
            frames=frames,
            fps=fps,
        )

        prompt_id = client.queue_prompt(workflow)
        outputs = client.wait_for_completion(prompt_id, timeout_seconds=1800.0)

        if not outputs:
            return None

        # Descargar primer archivo de salida
        first = outputs[0]
        filename   = first.get("filename", "")
        subfolder  = first.get("subfolder", "")
        ftype      = first.get("type", "output")

        if not filename:
            return None

        file_bytes = client.get_image(filename, subfolder, ftype)
        if not file_bytes:
            return None

        # Guardar en el directorio del job
        if not output_dir:
            output_dir = os.path.join(_base, "_videos", f"job_{job_id}")
        os.makedirs(output_dir, exist_ok=True)

        out_ext  = os.path.splitext(filename)[1] or ".webp"
        out_path = os.path.join(output_dir, f"scene_{scene_idx:02d}_anim{out_ext}")
        with open(out_path, "wb") as f:
            f.write(file_bytes)

        # Si el output es WEBP animado, convertir a MP4 via FFmpeg (con fallback a PIL para decodificar frames si falla)
        _ffmpeg = os.path.join(_base, "_integrations", "ffmpeg", "ffmpeg.exe")
        if not os.path.isfile(_ffmpeg):
            _ffmpeg = "ffmpeg"
            
        if out_ext.lower() in (".webp", ".gif"):
            mp4_path = out_path.replace(out_ext, ".mp4")
            
            # 1. Intentar conversión directa
            cmd = [
                _ffmpeg, "-y",
                "-i", out_path,
                "-c:v", "libx264", "-preset", "fast",
                "-pix_fmt", "yuv420p",
                mp4_path,
            ]
            try:
                extra_kwargs = {}
                if os.name == "nt":
                    creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
                    extra_kwargs["creationflags"] = creationflags

                r = subprocess.run(cmd, capture_output=True, timeout=60, **extra_kwargs)
                if r.returncode == 0 and os.path.isfile(mp4_path) and os.path.getsize(mp4_path) > 0:
                    os.remove(out_path)
                    return mp4_path
            except Exception:
                pass
                
            # 2. Fallback: Desempaquetar frames de WebP usando PIL y recomponer con FFmpeg
            # Inmuniza al sistema de limitaciones de decodificación nativa de WebP en FFmpeg
            try:
                import tempfile
                import shutil
                from PIL import Image
                
                temp_dir = tempfile.mkdtemp(prefix="webp_conv_")
                try:
                    with Image.open(out_path) as img:
                        frame_idx = 0
                        while True:
                            frame_path = os.path.join(temp_dir, f"frame_{frame_idx:05d}.png")
                            rgb_img = img.convert("RGB")
                            rgb_img.save(frame_path, "PNG")
                            frame_idx += 1
                            try:
                                img.seek(frame_idx)
                            except EOFError:
                                break
                    
                    cmd_seq = [
                        _ffmpeg, "-y",
                        "-r", str(fps),
                        "-i", os.path.join(temp_dir, "frame_%05d.png"),
                        "-c:v", "libx264", "-preset", "fast",
                        "-pix_fmt", "yuv420p",
                        mp4_path
                    ]
                    
                    extra_kwargs = {}
                    if os.name == "nt":
                        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)
                        extra_kwargs["creationflags"] = creationflags

                    r_seq = subprocess.run(cmd_seq, capture_output=True, timeout=60, **extra_kwargs)
                    if r_seq.returncode == 0 and os.path.isfile(mp4_path) and os.path.getsize(mp4_path) > 0:
                        os.remove(out_path)
                        return mp4_path
                finally:
                    shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception as e:
                log.error(f"[Animation Engine] WebP to MP4 PIL fallback failed: {e}")

            return out_path

        return out_path

    except Exception:
        return None

