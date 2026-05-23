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

