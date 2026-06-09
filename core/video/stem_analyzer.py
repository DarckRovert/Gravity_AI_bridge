import os
import numpy as np
import librosa
import scipy.signal
import logging

log = logging.getLogger("StemAnalyzer")

def analyze_stems(audio_path: str, fps: int = 24, target_duration_sec: float = None) -> dict:
    """
    Motor sensorial V19. Separa la música matemáticamente en 3 bandas:
    - 'mid' (Percusivo): Batería, golpes, kicks.
    - 'bass' (Armónico Bajo): Bajo, sub-bass, atmósferas graves (0-250Hz).
    - 'high' (Armónico Alto): Voces, sintetizadores, melodías (>250Hz).
    
    Retorna un diccionario retrocompatible con V18: {'bass': array, 'mid': array, 'high': array}
    """
    log.info(f"[StemAnalyzer] Extrayendo Stems Matemáticos vía HPSS para {os.path.basename(audio_path)}...")
    
    # Cargar audio eficientemente
    y, sr = librosa.load(audio_path, sr=None, mono=False, duration=target_duration_sec)
    
    # Mezclar a mono para HPSS
    y_mono = librosa.to_mono(y) if y.ndim == 2 else y
    
    if target_duration_sec is not None:
        target_frames = int(target_duration_sec * fps)
    else:
        target_frames = int(librosa.get_duration(y=y_mono, sr=sr) * fps)
        
    # 1. Aplicar HPSS (Harmonic-Percussive Source Separation)
    log.info("[StemAnalyzer] Aislando Batería (Percussive)...")
    y_h, y_p = librosa.effects.hpss(y_mono, margin=(1.0, 5.0))
    
    # 2. Extraer energía RMS Percusiva (Mapeado a 'mid' por retrocompatibilidad V18)
    rms_drums = librosa.feature.rms(y=y_p)[0]
    
    # 3. Separar el componente Armónico (y_h) en Graves (Bajo) y Agudos (Voces)
    log.info("[StemAnalyzer] Aislando Voces y Bajos (Harmonic)...")
    
    # Aplicar un filtro pasabajos de Butterworth a 250Hz para obtener el Bajo puro
    nyq = 0.5 * sr
    cutoff = 250.0 / nyq
    b_low, a_low = scipy.signal.butter(4, cutoff, btype='low')
    y_bass = scipy.signal.filtfilt(b_low, a_low, y_h)
    
    # Aplicar un filtro pasaaltos a 250Hz para obtener Voces/Melodía
    b_high, a_high = scipy.signal.butter(4, cutoff, btype='high')
    y_vocals = scipy.signal.filtfilt(b_high, a_high, y_h)
    
    # Extraer energía RMS
    rms_bass = librosa.feature.rms(y=y_bass)[0]
    rms_vocals = librosa.feature.rms(y=y_vocals)[0]
    
    # 4. Beat tracking y Paneo (Retrocompatibilidad total)
    tempo, beat_frames = librosa.beat.beat_track(y=y_mono, sr=sr, hop_length=int(sr/fps))
    beats = np.zeros(len(rms_bass))
    
    # Calcular paneo estéreo si es posible
    if y.ndim == 2:
        y_left, y_right = y[0], y[1]
        energy_L = librosa.feature.rms(y=y_left)[0]
        energy_R = librosa.feature.rms(y=y_right)[0]
        pan_raw = (energy_R - energy_L) / (energy_R + energy_L + 1e-8)
    else:
        pan_raw = np.zeros(len(rms_bass))

    # 5. Alinear longitudes con el FPS objetivo del video
    def align_to_fps(rms_array, target_len):
        rms_times = librosa.frames_to_time(np.arange(len(rms_array)), sr=sr)
        target_times = np.linspace(0, len(rms_array) * 512 / sr, target_len)
        return np.interp(target_times, rms_times, rms_array)
        
    aligned_drums = align_to_fps(rms_drums, target_frames)
    aligned_bass = align_to_fps(rms_bass, target_frames)
    aligned_vocals = align_to_fps(rms_vocals, target_frames)
    aligned_pan = align_to_fps(pan_raw, target_frames)
    
    # Re-mapear beats a la nueva longitud
    aligned_beats = np.zeros(target_frames)
    valid_beats = np.clip(np.round(beat_frames * (target_frames / len(beats))), 0, target_frames - 1).astype(int)
    aligned_beats[valid_beats] = 1.0
    for i in range(1, len(aligned_beats)):
        aligned_beats[i] = max(aligned_beats[i], aligned_beats[i-1] * 0.75)

    # 6. Normalizar al rango 0.0 - 1.0 y aplicar suavizado cinemático
    def normalize(arr, smooth=5):
        if np.max(arr) > 0:
            arr = arr / np.max(arr)
        window = np.ones(smooth)/smooth
        arr = np.convolve(arr, window, mode='same')
        return arr
        
    return {
        'bass': normalize(aligned_bass, 6),
        'mid': normalize(aligned_drums, 3),   
        'high': normalize(aligned_vocals, 8),
        'pan': normalize(aligned_pan, 2),
        'beat': aligned_beats
    }

if __name__ == "__main__":
    # Test Standalone
    test_file = r"F:\PROYECTO VIDEOCLIP MUSICAL\input\Horizonte de Eventos.mp3"
    if os.path.exists(test_file):
        stems = analyze_stems(test_file, fps=24, target_duration_sec=10.0)
        print("Bajo (0-250Hz) Max:", np.max(stems['bass']))
        print("Bateria (Percusivo) Max:", np.max(stems['mid']))
        print("Voz (Armonico >250Hz) Max:", np.max(stems['high']))
        print(f"Stems listos. Size: {len(stems['bass'])} frames.")
