import os
import numpy as np
from core.logger import log
from core.video.audio_analyzer import extract_multiband_energy


def apply_beat_synced_fx(
    video_path: str, audio_path: str, output_path: str, fps: int = 24
) -> bool:
    """
    Lee un video ya ensamblado y su audio original.
    Extrae la energía de los bajos y aplica efectos visuales (Zoom/Glitch)
    en los fotogramas donde el ritmo explota (beat_hit).
    """
    try:
        from moviepy import VideoFileClip
    except ImportError as e:
        log.error(f"[BeatSyncer] Error importando MoviePy (v2): {e}")
        return False

    if not os.path.isfile(video_path) or not os.path.isfile(audio_path):
        log.error(
            "[BeatSyncer] Faltan archivos de video o audio para la sincronización."
        )
        return False

    log.info(
        "[BeatSyncer] Analizando frecuencias de audio para inyectar transiciones rítmicas..."
    )
    multiband = extract_multiband_energy(audio_path, fps)

    bass_energy = multiband.get("bass", [])
    if not len(bass_energy):
        log.warning(
            "[BeatSyncer] No se detectó energía de graves. Saltando FX rítmico."
        )
        return False

    # Detectar picos (beat drops)
    # Un beat hit es cuando la energía del bajo excede significativamente su media móvil local.
    beats = np.zeros(len(bass_energy))
    window = int(fps * 0.5)  # Media móvil de 0.5 segundos
    for i in range(len(bass_energy)):
        start = max(0, i - window)
        local_mean = np.mean(bass_energy[start : i + 1])
        # Si el bajo actual es un 40% mayor que la media local y alto en absoluto
        if bass_energy[i] > local_mean * 1.4 and bass_energy[i] > 0.4:
            beats[i] = 1.0

    # Para evitar ráfagas de beats (muchos en un solo segundo), aplicamos un enfriamiento
    cooldown = 0
    for i in range(len(beats)):
        if cooldown > 0:
            beats[i] = 0
            cooldown -= 1
        elif beats[i] == 1.0:
            cooldown = int(fps * 0.3)  # 0.3s cooldown

    # Cargar el clip de video
    try:
        clip = VideoFileClip(video_path)
    except Exception as e:
        log.error(f"[BeatSyncer] Error cargando video en MoviePy: {e}")
        return False

    def process_frame(get_frame, t):
        frame = get_frame(t)
        frame_idx = int(t * fps)
        if frame_idx >= len(beats):
            return frame

        beat_val = beats[frame_idx]
        if beat_val == 1.0:
            # Reemplazamos el Glitch RGB por un Flash de Exposición intenso pero nítido
            # Esto evita el desenfoque y no arruina los subtítulos
            glitched = np.clip(frame * 1.35, 0, 255).astype(np.uint8)
            return glitched

        return frame

    log.info(
        "[BeatSyncer] Inyectando efectos de Chromatic Aberration en los Beat Drops..."
    )
    processed_clip = clip.transform(process_frame)
    processed_clip = processed_clip.with_audio(clip.audio)

    try:
        processed_clip.write_videofile(
            output_path,
            codec="h264_amf",
            audio_codec="aac",
            temp_audiofile="temp-audio.m4a",
            remove_temp=True,
            fps=fps,
            logger=None,  # Silenciar logs de MoviePy
        )
        clip.close()
        processed_clip.close()
        log.info(f"[BeatSyncer] Exportación rítmica completada: {output_path}")
        return True
    except Exception as e:
        log.error(f"[BeatSyncer] Falló exportación en MoviePy: {e}")
        clip.close()
        return False
