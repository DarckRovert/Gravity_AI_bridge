import sys
import os
import numpy as np
import soundfile as sf

sys.path.append('f:/Gravity_AI_bridge')
from core.video.procedural_generator import generate_procedural_video

out_dir = 'F:/PROYECTO VIDEOCLIP MUSICAL/input'
os.makedirs(out_dir, exist_ok=True)

# 1. Generar un beat sintético de 4 segundos a 120 BPM
sample_rate = 44100
duration = 4.0
t = np.linspace(0, duration, int(sample_rate * duration), endpoint=False)

# Kick drum sintético (frecuencia bajando rápidamente)
beat_interval = 60 / 120  # 120 BPM = 0.5 sec por beat
audio_signal = np.zeros_like(t)

for beat_time in np.arange(0, duration, beat_interval):
    # Envolvente exponencial corta
    beat_t = t[(t >= beat_time) & (t < beat_time + 0.3)] - beat_time
    envelope = np.exp(-15.0 * beat_t)
    # Frecuencia bajando de 150Hz a 40Hz
    freq = 40 + 110 * np.exp(-30.0 * beat_t)
    phase = 2 * np.pi * np.cumsum(freq) / sample_rate
    kick = np.sin(phase) * envelope
    
    idx_start = int(beat_time * sample_rate)
    idx_end = idx_start + len(kick)
    audio_signal[idx_start:idx_end] += kick * 0.8

# Guardar el beat como WAV
audio_path = os.path.join(out_dir, 'synthetic_beat.wav')
sf.write(audio_path, audio_signal, sample_rate)
print(f"Audio de prueba generado en: {audio_path}")

# 2. Generar video Audio-Reactivo V5
video_path = os.path.join(out_dir, 'video_fractal_v5_audioreactive.mp4')
generate_procedural_video('dark cosmic horror fractal magic', 7777, 1280, 720, 4, 24, video_path, audio_path=audio_path)

print(f"¡Prueba V5 Audio-Reactiva completada con éxito!")
