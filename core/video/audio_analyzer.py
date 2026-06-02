import os
import numpy as np

def extract_multiband_energy(audio_path: str, fps: int = 24) -> dict:
    """
    V7: Analiza el audio y extrae curvas espectrales (Bajos, Medios, Altos) + Paneo Estéreo.
    Devuelve {'bass': arr, 'mid': arr, 'high': arr, 'pan': arr}.
    'pan' va de -1.0 (Izquierda total) a +1.0 (Derecha total).
    """
    if not audio_path or not os.path.isfile(audio_path):
        return {'bass': np.array([]), 'mid': np.array([]), 'high': np.array([]), 'pan': np.array([])}
        
    try:
        import librosa
        # mono=False para intentar capturar el estéreo (shape = [2, n_samples])
        y, sr = librosa.load(audio_path, sr=None, mono=False)
        hop_length = int(sr / fps)
        
        # Mezclar a mono para el análisis frecuencial
        if y.ndim == 2:
            y_mono = librosa.to_mono(y)
            y_left = y[0]
            y_right = y[1]
        else:
            y_mono = y
            y_left = y
            y_right = y
            
        # Calcular espectrograma (mono)
        S = np.abs(librosa.stft(y_mono, hop_length=hop_length))
        frequencies = librosa.fft_frequencies(sr=sr)
        
        # Índices de frecuencias
        bass_idx = np.where((frequencies >= 20) & (frequencies <= 250))[0]
        mid_idx = np.where((frequencies > 250) & (frequencies <= 2000))[0]
        high_idx = np.where((frequencies > 2000) & (frequencies <= 20000))[0]
        
        bass = np.sum(S[bass_idx, :], axis=0) if len(bass_idx) > 0 else np.zeros(S.shape[1])
        mid = np.sum(S[mid_idx, :], axis=0) if len(mid_idx) > 0 else np.zeros(S.shape[1])
        high = np.sum(S[high_idx, :], axis=0) if len(high_idx) > 0 else np.zeros(S.shape[1])
        
        # Paneo Estéreo
        S_left = np.abs(librosa.stft(y_left, hop_length=hop_length))
        S_right = np.abs(librosa.stft(y_right, hop_length=hop_length))
        
        energy_L = np.sum(S_left, axis=0)
        energy_R = np.sum(S_right, axis=0)
        # Pan: -1 (izq) a 1 (der)
        pan_raw = (energy_R - energy_L) / (energy_R + energy_L + 1e-8)
        
        def normalize_and_smooth(arr, smooth_factor=6, is_pan=False):
            if not is_pan:
                arr_min = np.min(arr)
                arr_max = np.max(arr)
                if arr_max > arr_min:
                    arr = (arr - arr_min) / (arr_max - arr_min + 1e-8)
                else:
                    arr = np.zeros_like(arr)
            
            window_size = max(1, fps // smooth_factor)
            if window_size > 1:
                window = np.ones(window_size) / window_size
                arr = np.convolve(arr, window, mode='same')
            return arr
            
        return {
            'bass': normalize_and_smooth(bass, 6),
            'mid': normalize_and_smooth(mid, 3),
            'high': normalize_and_smooth(high, 8),
            'pan': normalize_and_smooth(pan_raw, 2, is_pan=True) # Paneo muy suave
        }
        
    except Exception as e:
        print(f"[AudioAnalyzer V7] Error procesando audio: {e}")
        return {'bass': np.array([]), 'mid': np.array([]), 'high': np.array([]), 'pan': np.array([])}

def extract_audio_energy(audio_path: str, fps: int = 24) -> np.ndarray:
    """Fallback legacy compatible con V5"""
    res = extract_multiband_energy(audio_path, fps)
    if len(res['bass']) > 0:
        return (res['bass'] + res['mid'] + res['high']) / 3.0
    return np.array([])

