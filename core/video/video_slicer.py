import os
import subprocess
import logging
from core.video.ffmpeg_utils import get_ffmpeg_exe

log = logging.getLogger(__name__)

def extract_clips_from_video(
    input_video_path: str,
    output_dir: str,
    n_scenes: int,
    scene_duration: float,
    target_w: int,
    target_h: int,
    fps: int = 24
) -> list[str]:
    """
    Toma un video de entrada y lo recorta en 'n_scenes' clips, cada uno de 'scene_duration' segundos.
    Escala y recorta los clips a target_w x target_h (crop center) para llenar la pantalla.
    Retorna la lista de rutas de los clips extraídos.
    """
    ffmpeg_exe = get_ffmpeg_exe()
    os.makedirs(output_dir, exist_ok=True)
    clips = []

    # Validar que el video existe
    if not os.path.isfile(input_video_path):
        log.error(f"[VideoSlicer] Video de entrada no encontrado: {input_video_path}")
        return clips

    # Averiguar duración total del input video
    try:
        probe_cmd = [
            ffmpeg_exe.replace("ffmpeg.exe", "ffprobe.exe").replace("ffmpeg", "ffprobe"),
            "-v", "error", "-show_entries", "format=duration", "-of",
            "default=noprint_wrappers=1:nokey=1", input_video_path
        ]
        total_dur_str = subprocess.check_output(probe_cmd, text=True).strip()
        total_duration = float(total_dur_str)
    except Exception as e:
        log.warning(f"[VideoSlicer] No se pudo leer duración de {input_video_path}. Asumiendo 999s. Error: {e}")
        total_duration = 999.0

    half_dur = scene_duration / 2.0
    log.info(f"[VideoSlicer] Procesando {input_video_path} ({total_duration}s) -> {n_scenes} clips de {half_dur}s")

    for i in range(1, n_scenes + 1):
        start_time = (i - 1) * scene_duration
        
        # Si el inicio del clip excede la duración del video, hacer loop desde el principio
        if start_time >= total_duration:
            start_time = start_time % total_duration

        clip_path = os.path.join(output_dir, f"scene_{i:02d}_userclip.mp4")
        
        cmd = [
            ffmpeg_exe, "-y",
            "-ss", str(start_time),
            "-i", input_video_path,
            "-t", str(half_dur),
            "-vf", f"scale={target_w}:{target_h}:force_original_aspect_ratio=increase,crop={target_w}:{target_h},fps={fps}",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-color_range", "tv",
            "-colorspace", "bt709",
            "-color_trc", "bt709",
            "-color_primaries", "bt709",
            "-an", # Sin audio, el ensamblador le pondrá la música
            clip_path
        ]

        try:
            subprocess.run(cmd, capture_output=True, check=True)
            clips.append(clip_path)
            log.info(f"[VideoSlicer] Clip extraído: {os.path.basename(clip_path)} (Inicio: {start_time}s)")
        except subprocess.CalledProcessError as e:
            log.error(f"[VideoSlicer] Error extrayendo clip {i}: {e.stderr.decode('utf-8', errors='ignore')}")
            # Fallback en caso de error: meter string vacío para que la pipeline sepa que falló
            clips.append("")

    return clips
