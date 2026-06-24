import numpy as np


def generate_timeline(multiband: dict, fps: int = 24) -> list:
    """
    V8: Genera una línea de tiempo con 5 motores posibles y añade tiempos de transición
    para Crossfade (solapamiento de escenas).
    """
    if not multiband["bass"].size:
        return []

    total_frames = len(multiband["bass"])
    total_power = (
        multiband["bass"] * 1.5 + multiband["mid"] + multiband["high"] * 0.5
    ) / 3.0

    window_size = fps * 10
    if window_size > total_frames:
        window_size = max(1, total_frames // 2)

    window = np.ones(window_size) / window_size
    smoothed_power = np.convolve(total_power, window, mode="same")

    max_power = np.max(smoothed_power)
    t_drop = max_power * 0.80
    t_high = max_power * 0.60
    t_med = max_power * 0.35
    t_low = max_power * 0.15

    timeline = []
    current_engine = "space_odyssey"
    start_idx = 0
    min_frames_per_scene = fps * 12  # 12 segundos mínimo por escena

    for i in range(min_frames_per_scene, total_frames, min_frames_per_scene // 2):
        prev_p = smoothed_power[i - fps * 2]
        curr_p = smoothed_power[i]

        # Lógica ampliada V8
        if curr_p > t_drop and prev_p <= t_drop:
            new_engine = "quantum_tunnel"  # Máxima agresividad
        elif curr_p > t_high and prev_p <= t_high:
            new_engine = "mandelbulb"  # Gran detalle
        elif curr_p > t_med and prev_p <= t_med:
            new_engine = "julia_fractal"  # Tensión media
        elif curr_p > t_low and prev_p <= t_low:
            new_engine = "nebula"  # Calma mística
        elif curr_p <= t_low and prev_p > t_low:
            new_engine = "space_odyssey"  # Intro / Outro profundo
        else:
            new_engine = current_engine

        if new_engine != current_engine and (i - start_idx) >= min_frames_per_scene:
            timeline.append({"start": start_idx, "end": i, "engine": current_engine})
            start_idx = i
            current_engine = new_engine

    timeline.append({"start": start_idx, "end": total_frames, "engine": current_engine})

    # Inyectar tiempos de transición (Crossfade de 2 segundos)
    crossfade_frames = fps * 2
    for i in range(len(timeline) - 1):
        timeline[i]["transition_start"] = timeline[i]["end"] - crossfade_frames
        timeline[i + 1]["incoming_end"] = timeline[i + 1]["start"] + crossfade_frames

    return timeline


def generate_color_sequence(total_frames: int, multiband: dict, fps: int = 24) -> tuple:
    """
    V8: Genera dos arrays RGB a lo largo del tiempo.
    En baja energía: Tonos fríos (Azul/Cian/Morado)
    En alta energía: Tonos calientes (Rojo/Naranja/Oro)
    """
    smoothed_energy = multiband["bass"] * 0.7 + multiband["mid"] * 0.3
    window = np.ones(fps * 2) / (fps * 2)
    smoothed_energy = np.convolve(smoothed_energy, window, mode="same")

    colorsA = np.zeros((total_frames, 3), dtype=np.float32)
    colorsB = np.zeros((total_frames, 3), dtype=np.float32)

    cold_A = np.array([0.02, 0.05, 0.20])
    cold_B = np.array([0.10, 0.30, 0.50])

    hot_A = np.array([0.50, 0.10, 0.05])
    hot_B = np.array([0.90, 0.60, 0.10])

    for i in range(total_frames):
        t = min(1.0, smoothed_energy[i] * 2.0)  # Normalizar el "calor"
        colorsA[i] = cold_A * (1.0 - t) + hot_A * t
        colorsB[i] = cold_B * (1.0 - t) + hot_B * t

    return colorsA, colorsB
