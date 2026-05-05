"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY AI — ANIMATION ENGINE V1.0                                         ║
║  Motor de Animación de Imágenes (MAI) — Gravity Studio V12.2 PRO               ║
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
    """Ken Burns extendido con 6 variantes rotativas."""
    variant_fn = _KB_VARIANTS[scene_idx % len(_KB_VARIANTS)]
    z, x, y = variant_fn(total_frames, w, h)
    return (
        f"zoompan=z='{z}':d={total_frames}"
        f":x='{x}':y='{y}'"
        f":s={w}x{h}:fps={fps}"
    )


def _build_pulse(total_frames: int, w: int, h: int, fps: int, clip_dur: float) -> str:
    """
    Efecto de respiración: zoom oscilante sinusoidal suave.
    Escala entre 1.0 y 1.06 con período de ~4s.
    """
    # zoompan con zoom = 1.03 + 0.03*sin(on/fps * 2*pi/period)
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
    Deriva lenta de cámara + viñeta. Pan horizontal sutil.
    Alternado entre izquierda y derecha según escena_idx.
    Implementado con zoompan (variable 'on' disponible) en lugar de crop.
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
    Efecto glitch: desfase de canales RGB + grano digital intermitente.
    Sutil: rgbashift limitado para no romper la composición.
    """
    # rgbashift: desplaza R y B levemente, independiente
    return (
        f"scale={w}:{h}:force_original_aspect_ratio=decrease,"
        f"pad={w}:{h}:(ow-iw)/2:(oh-ih)/2:black,"
        f"fps={fps},"
        f"rgbashift=rh=2:bh=-2:rv=1:bv=-1,"
        f"noise=alls=4:allf=t"
    )


def _build_film_burn(total_frames: int, w: int, h: int, fps: int, clip_dur: float) -> str:
    """
    Quemado de película analógico: fade-in con overexposición + grano.
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
    Temblor de cámara handheld: crop con offset sinusoidal en X e Y.
    Intensidad moderada para no marear.
    Usa 'n' (frame number en filtro crop) en lugar de 'on' (exclusivo de zoompan).
    """
    shake_px = max(4, min(12, w // 100))  # 1% del ancho, mín 4px, máx 12px
    freq = 3.5  # Hz de vibración
    frames_per_cycle = max(1, int(fps / freq))
    # Pad para dar margen al shake
    pad = shake_px * 2
    # 'n' es el número de frame en el filtro crop (equivalente a 'on' en zoompan)
    x_expr = f"({shake_px}*sin(2*PI*n/{frames_per_cycle}))+{shake_px}"
    y_expr = f"({shake_px // 2}*cos(2*PI*n/{frames_per_cycle}))+{shake_px // 2}"
    return (
        f"scale={w + pad}:{h + pad}:force_original_aspect_ratio=increase,"
        f"crop={w}:{h}:'{x_expr}':'{y_expr}',"
        f"fps={fps}"
    )


def _build_tilt_shift(w: int, h: int, fps: int) -> str:
    """
    Tilt-Shift simplificado: desenfoque suave en toda la imagen
    + vignette para reforzar el efecto de profundidad de campo.
    La implementación con split/overlay requiere alphamerge que no está
    disponible en todos los builds de FFmpeg, por lo que usamos
    boxblur leve + vignette como aproximación segura y universal.
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
    Parallax simulado: escala la imagen más de lo necesario y hace
    pan en dirección opuesta a velocidad mayor (simula profundidad).
    Usa 'n' (frame number en filtro crop) en lugar de 'on' (exclusivo de zoompan).
    """
    direction = 1 if scene_idx % 2 == 0 else -1
    scale_factor = 1.25
    pan_pct = 0.08
    sw = int(w * scale_factor)
    sh = int(h * scale_factor)
    x_offset = (sw - w) // 2
    y_offset = (sh - h) // 2
    pan_px = int(sw * pan_pct)
    # 'n' es el número de frame en el filtro crop (correcto)
    x_expr = f"{x_offset}+({direction}*{pan_px}*n/{total_frames})"
    return (
        f"scale={sw}:{sh}:force_original_aspect_ratio=increase,"
        f"crop={w}:{h}:'{x_expr}':{y_offset},"
        f"fps={fps}"
    )


# ── Motor L2: ComfyUI / AnimateDiff ──────────────────────────────────────────

def animate_with_comfyui(
    image_path: str,
    job_id: int,
    scene_idx: int,
    fps: int = 8,
    frames: int = 16,
    output_dir: str = "",
) -> Optional[str]:
    """
    Intenta generar un clip MP4 animado a partir de una imagen usando
    ComfyUI con el workflow Image-to-Video (LTX-Video).

    Returns:
        Ruta al archivo MP4 generado, o None si falla (pipeline hace fallback a L1).
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
        client = ComfyUIClient()

        if not client.is_online():
            return None

        # Determinar resolución desde la imagen
        w, h = 512, 512
        try:
            from PIL import Image
            with Image.open(image_path) as img:
                w, h = img.size
                # Reducir para ComfyUI (cost computacional)
                if w > 768:
                    scale = 768 / w
                    w = 768
                    h = int(h * scale)
                    h = h - (h % 8)  # múltiplo de 8
                    w = w - (w % 8)
        except Exception:
            pass

        workflow = client.build_img2video_workflow(
            image_path=image_path,
            width=w,
            height=h,
            frames=frames,
            fps=fps,
        )

        prompt_id = client.queue_prompt(workflow)
        outputs = client.wait_for_completion(prompt_id, timeout_seconds=300.0)

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

        # Si el output es WEBP animado, convertir a MP4 via FFmpeg
        # Usar el mismo FFMPEG_EXE que define el pipeline principal
        _ffmpeg = os.path.join(_base, "_integrations", "ffmpeg", "ffmpeg.exe")
        if not os.path.isfile(_ffmpeg):
            # Fallback: ffmpeg en PATH del sistema
            _ffmpeg = "ffmpeg"
        if out_ext.lower() in (".webp", ".gif"):
            mp4_path = out_path.replace(out_ext, ".mp4")
            cmd = [
                _ffmpeg, "-y",
                "-i", out_path,
                "-c:v", "libx264", "-preset", "fast",
                "-pix_fmt", "yuv420p",
                mp4_path,
            ]
            try:
                r = subprocess.run(cmd, capture_output=True, timeout=60,
                                   creationflags=subprocess.CREATE_NO_WINDOW)
                if r.returncode == 0 and os.path.isfile(mp4_path):
                    os.remove(out_path)
                    return mp4_path
            except Exception:
                pass
            return out_path

        return out_path

    except Exception:
        return None
