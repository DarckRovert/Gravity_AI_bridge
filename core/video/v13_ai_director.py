import json
import re
import numpy as np
from core.logger import log
from typing import Optional


def _parse_color_any(c_val):
    """Parsea color desde lista [R,G,B], hex string o CSV string."""
    if isinstance(c_val, list) and len(c_val) >= 3:
        return [float(x) for x in c_val[:3]]
    if isinstance(c_val, str):
        c_val = c_val.strip()
        if c_val.startswith("#"):
            h = c_val.lstrip("#")
            if len(h) == 6:
                return [int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4)]
        if "," in c_val:
            parts = c_val.split(",")
            if len(parts) >= 3:
                return [float(x) for x in parts[:3]]
    return None


def _query_llm(
    section_label: str, section_text: str, provider: Optional[str] = None, model: Optional[str] = None
) -> dict:
    """
    Consulta al modelo local para una sección específica de la letra.
    Devuelve dict con u_baseColor1, u_baseColor2, speed_multiplier, turbulence, engine y pose.
    """
    from core import provider_manager

    system_prompt = (
        "Eres el Director de Efectos Visuales V13.\n"
        "Analiza el fragmento de letra (y el contexto global de la canción si es necesario) y devuelve ÚNICAMENTE un objeto JSON válido.\n"
        "Sin markdown, sin texto adicional, solo el JSON.\n\n"
        "Formato exacto:\n"
        "{\n"
        '  "engine": "space_odyssey",\n'
        '  "custom_scene_prompt": "Descripción cinematográfica fotorrealista del entorno de fondo (ej: majestic ruins of Machu Picchu hidden in the clouds at golden hour, epic inca architecture, hyperrealistic)",\n'
        '  "pose": 1,\n'
        '  "u_baseColor1": [R, G, B],\n'
        '  "u_baseColor2": [R, G, B],\n'
        '  "speed_multiplier": 1.0,\n'
        '  "turbulence": 1.0\n'
        "}\n\n"
        "Notas sobre custom_scene_prompt:\n"
        "- Debe ser en inglés, descriptivo y enfocado a generar una imagen fotorealista espectacular (evita descripciones de personas, enfócate en el paisaje/entorno).\n"
        "- Adáptalo fielmente a la vibra de la letra (ej: si es andino, usa selvas, montañas, ruinas incas; si es cyber, usa ciudades de neón).\n\n"
        "Opciones de engine (Para los efectos de partículas superpuestos):\n"
        "- inca_math: Ruinas, montañas, arquitectura antigua, épico, majestuoso.\n"
        "- space_odyssey: Intro, soledad, desierto.\n"
        "- nebula: Coros etéreos, calma, espiritual.\n"
        "- julia_fractal: Tensión, dudas, laberinto mental.\n"
        "- mandelbulb: Revelaciones profundas, complejidad.\n"
        "- quantum_tunnel: Clímax, velocidad caótica, agresión pura.\n\n"
        "Opciones de pose (int):\n"
        "- 0: Parado, melancolía, observando.\n"
        "- 1: Caminando heroicamente, determinación.\n"
        "- 2: Volando inerte, cayendo por un túnel, dejarse llevar.\n\n"
        "R,G,B = floats 0.0-1.0. speed_multiplier: 0.5 a 2.0. turbulence: 0.5 a 1.8."
    )
    messages = [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": f"Sección '{section_label}':\n{section_text[:800]}",
        },
    ]

    response_text = provider_manager.complete(
        messages,
        model=model,
        provider=provider,
        task="reason",
        options={"temperature": 0.3, "max_tokens": 200},
    )

    # Remover bloques <think> de modelos de razonamiento (DeepSeek/Gemma R1)
    clean_text = re.sub(r"<think>.*?</think>", "", response_text, flags=re.DOTALL)

    start_idx = clean_text.find("{")
    end_idx = clean_text.rfind("}")
    if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
        return json.loads(clean_text[start_idx : end_idx + 1])

    return {}


def _split_lyrics_into_sections(lyrics: str) -> list[tuple[str, str]]:
    """
    Divide la letra en secciones basadas en líneas vacías o etiquetas.
    Devuelve lista de (label, text) por sección.
    """
    sections = []
    current_lines = []
    section_idx = 1

    for line in lyrics.splitlines():
        stripped = line.strip()
        # Línea en mayúsculas entre corchetes = etiqueta de sección
        if stripped.startswith("[") and stripped.endswith("]"):
            if current_lines:
                sections.append((f"Sección {section_idx}", "\n".join(current_lines)))
                section_idx += 1
            current_lines = [stripped]
        elif stripped == "" and current_lines:
            # Párrafo vacío = nueva sección
            sections.append((f"Sección {section_idx}", "\n".join(current_lines)))
            section_idx += 1
            current_lines = []
        else:
            current_lines.append(stripped)

    if current_lines:
        sections.append((f"Sección {section_idx}", "\n".join(current_lines)))

    # Si hay más de 6 secciones, agrupar de a 2
    if len(sections) > 6:
        merged = []
        for i in range(0, len(sections), 2):
            pair = sections[i : i + 2]
            label = pair[0][0]
            text = "\n".join([p[1] for p in pair])
            merged.append((label, text))
        sections = merged

    return sections


def analyze_lyrics_for_v13(lyrics: str) -> dict:
    """
    Análisis global (compatibilidad hacia atrás).
    Devuelve parámetros para el video completo.
    """
    if not lyrics or len(lyrics.strip()) < 10:
        return {}
    try:
        result = _query_llm("Canción completa", lyrics[:2000])
        log.info(f"[V13 Director] Análisis global completado: {result}")
        return result
    except Exception as e:
        log.warning(f"[V13 Director] Error en análisis global: {e}")
        return {}


def analyze_lyrics_sections(lyrics: str, total_frames: int, fps: int) -> dict:
    """
    Análisis narrativo por secciones. Devuelve un dict con:
    - colorsA, colorsB, speed, turbulence (arrays por frame)
    - timeline (lista dict) con el storyboard exacto (engine, pose, transiciones).
    """
    if not lyrics or len(lyrics.strip()) < 10 or total_frames == 0:
        return {}

    sections = _split_lyrics_into_sections(lyrics)
    log.info(f"[V13 Director] Analizando {len(sections)} secciones narrativas...")

    # Defaults si el LLM falla
    DEFAULT_C1 = [0.1, 0.05, 0.3]
    DEFAULT_C2 = [0.4, 0.1, 0.6]
    DEFAULT_SPD = 1.0
    DEFAULT_TRB = 1.0
    DEFAULT_ENG = "space_odyssey"
    DEFAULT_POSE = 0

    keyframes_c1 = []
    keyframes_c2 = []
    keyframes_spd = []
    keyframes_trb = []
    keyframe_frames = []

    timeline = []

    n = len(sections)
    frames_per_section = total_frames / n
    crossfade_frames = fps * 2

    import concurrent.futures
    from core import provider_manager

    # Get all healthy providers for Swarm Round-Robin
    all_results = provider_manager.scan_all()
    healthy_providers = []
    for r in all_results:
        if r.is_healthy and r.models:
            healthy_providers.append((r.name, r.active_model or r.models[0]["name"]))

    if not healthy_providers:
        log.warning(
            "[V13 Director Swarm] No hay proveedores IA saludables. Se usaran defaults."
        )
        healthy_providers = [(None, None)]

    def process_section(idx, label, text):
        prov, mod = healthy_providers[idx % len(healthy_providers)]
        try:
            params = _query_llm(label, text, provider=prov, model=mod)
            return idx, label, params, prov, mod
        except Exception as e:
            log.warning(f"[V13 Director Swarm] Error en '{label}': {e}")
            return idx, label, {}, prov, mod

    results_unsorted = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=len(sections)) as executor:
        futures = [
            executor.submit(process_section, i, label, text)
            for i, (label, text) in enumerate(sections)
        ]
        for fut in concurrent.futures.as_completed(futures):
            results_unsorted.append(fut.result())

    results_sorted = sorted(results_unsorted, key=lambda x: x[0])

    # --- EXECUTIVE PRODUCER NODE ---
    if len(results_sorted) > 1:
        try:
            import json

            raw_scenes = []
            for idx, label, params, prov, mod in results_sorted:
                raw_scenes.append({"label": label, "params": params, "brain": mod})

            exec_prompt = (
                "Eres el Productor Ejecutivo V14.\n"
                "Abajo hay una lista de escenas JSON generadas por un enjambre de IAs creativas. "
                "Tu trabajo es ARMONIZAR la paleta de colores (u_baseColor1, u_baseColor2) y la velocidad (speed_multiplier) "
                "para que el videoclip tenga coherencia visual y no parezca un error grafico, pero conservando la intencion de cada escena.\n"
                "Devuelve UNICAMENTE un array JSON con los objetos 'params' modificados, en el mismo orden exacto.\n\n"
                f"Escenas:\n{json.dumps(raw_scenes, indent=2)}"
            )
            messages = [
                {
                    "role": "system",
                    "content": "You are the Executive Producer. Output ONLY a valid JSON array of objects.",
                },
                {"role": "user", "content": exec_prompt},
            ]
            log.info(
                "[V13 Director Swarm] Evaluando consenso con el Productor Ejecutivo..."
            )

            # Usar el mejor modelo disponible para razonamiento
            exec_response = provider_manager.complete(
                messages,
                task="reason",
                options={"temperature": 0.1, "max_tokens": 1500},
            )

            # Limpieza
            clean_text = re.sub(
                r"<think>.*?</think>", "", exec_response, flags=re.DOTALL
            )
            start_idx = clean_text.find("[")
            end_idx = clean_text.rfind("]")

            if start_idx != -1 and end_idx != -1:
                harmonized_params = json.loads(clean_text[start_idx : end_idx + 1])
                if len(harmonized_params) == len(results_sorted):
                    for idx in range(len(results_sorted)):
                        orig = results_sorted[idx]
                        results_sorted[idx] = (
                            orig[0],
                            orig[1],
                            harmonized_params[idx],
                            "ExecutiveProducer",
                            "Consensus",
                        )
                    log.info(
                        "[V13 Director Swarm] Productor Ejecutivo aplico armonizacion con exito."
                    )
        except Exception as e:
            log.warning(
                f"[V13 Director Swarm] Productor Ejecutivo fallo (usando cortes puros): {e}"
            )
    # -------------------------------

    for i, label, params, prov, mod in results_sorted:
        start_frame = int(i * frames_per_section)
        end_frame = int((i + 1) * frames_per_section) if i < n - 1 else total_frames - 1

        c1 = _parse_color_any(params.get("u_baseColor1")) or DEFAULT_C1
        c2 = _parse_color_any(params.get("u_baseColor2")) or DEFAULT_C2
        spd = float(params.get("speed_multiplier", DEFAULT_SPD))
        trb = float(params.get("turbulence", DEFAULT_TRB))
        engine = params.get("engine", DEFAULT_ENG)
        pose = int(params.get("pose", DEFAULT_POSE))
        custom_scene_prompt = params.get("custom_scene_prompt", "")
        prov_name = prov if prov else "Default"
        log.info(
            f"[V13 Director Swarm] '{label}' [Brain: {prov_name} / {mod}]: {engine}(pose={pose}) C1={c1} spd={spd:.2f}"
        )

        # Añadir al timeline narrativo
        scene = {
            "start": start_frame,
            "end": end_frame,
            "engine": engine,
            "pose": pose,
            "custom_scene_prompt": custom_scene_prompt,
        }

        # Calcular crossfades con la escena anterior
        if i > 0:
            timeline[i - 1]["transition_start"] = (
                timeline[i - 1]["end"] - crossfade_frames
            )
            scene["incoming_end"] = scene["start"] + crossfade_frames

        timeline.append(scene)

        mid_frame = int(start_frame + (end_frame - start_frame) / 2)
        keyframe_frames.append(mid_frame)
        keyframes_c1.append(c1)
        keyframes_c2.append(c2)
        keyframes_spd.append(spd)
        keyframes_trb.append(trb)

    # IMPONER CUOTA INCA MATH (Garantizar que al menos el 50% sea Inca)
    if len(timeline) == 1:
        # Si la canción es tan corta que solo tiene 1 sección, dividirla por la mitad
        half = timeline[0]["end"] // 2

        scene2 = timeline[0].copy()
        scene2["start"] = half
        scene2["engine"] = (
            "space_odyssey"
            if timeline[0]["engine"] == "inca_math"
            else timeline[0]["engine"]
        )

        timeline[0]["end"] = half
        timeline[0]["engine"] = "inca_math"

        # Calcular transición
        timeline[0]["transition_start"] = half - crossfade_frames
        scene2["incoming_end"] = half + crossfade_frames
        timeline.append(scene2)
    else:
        for idx in range(len(timeline)):
            if idx % 2 == 0:
                timeline[idx]["engine"] = "inca_math"

    # Añadir keyframe al inicio y al final para que la interpolación cubra todo
    keyframe_frames = [0] + keyframe_frames + [total_frames - 1]
    keyframes_c1 = [keyframes_c1[0]] + keyframes_c1 + [keyframes_c1[-1]]
    keyframes_c2 = [keyframes_c2[0]] + keyframes_c2 + [keyframes_c2[-1]]
    keyframes_spd = [keyframes_spd[0]] + keyframes_spd + [keyframes_spd[-1]]
    keyframes_trb = [keyframes_trb[0]] + keyframes_trb + [keyframes_trb[-1]]

    all_frames = np.arange(total_frames)

    # Interpolación cúbica (smooth easing) para colores y escalares
    from scipy.interpolate import PchipInterpolator

    kf = np.array(keyframe_frames, dtype=float)

    def interp_channel(vals):
        return PchipInterpolator(kf, np.array(vals, dtype=float))(all_frames)

    c1_r = np.clip(interp_channel([c[0] for c in keyframes_c1]), 0, 1)
    c1_g = np.clip(interp_channel([c[1] for c in keyframes_c1]), 0, 1)
    c1_b = np.clip(interp_channel([c[2] for c in keyframes_c1]), 0, 1)

    c2_r = np.clip(interp_channel([c[0] for c in keyframes_c2]), 0, 1)
    c2_g = np.clip(interp_channel([c[1] for c in keyframes_c2]), 0, 1)
    c2_b = np.clip(interp_channel([c[2] for c in keyframes_c2]), 0, 1)

    spd_arr = np.clip(interp_channel(keyframes_spd), 0.3, 3.0)
    trb_arr = np.clip(interp_channel(keyframes_trb), 0.3, 2.5)

    colorsA = np.stack([c1_r, c1_g, c1_b], axis=1).astype(np.float32)
    colorsB = np.stack([c2_r, c2_g, c2_b], axis=1).astype(np.float32)

    return {
        "colorsA": colorsA,
        "colorsB": colorsB,
        "speed": spd_arr.astype(np.float32),
        "turbulence": trb_arr.astype(np.float32),
        "timeline": timeline,
    }
