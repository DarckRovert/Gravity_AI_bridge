filepath = r"f:\Gravity_AI_bridge\core\video\v13_ai_director.py"

with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Update _query_llm definition and call
if (
    "def _query_llm(section_label: str, section_text: str, provider: str = None, model: str = None) -> dict:"
    not in content
):
    content = content.replace(
        "def _query_llm(section_label: str, section_text: str) -> dict:",
        "def _query_llm(section_label: str, section_text: str, provider: str = None, model: str = None) -> dict:",
        1,
    )

old_complete = """    response_text = provider_manager.complete(
        messages,
        task="reason",
        options={"temperature": 0.3, "max_tokens": 200}
    )"""

new_complete = """    response_text = provider_manager.complete(
        messages,
        model=model,
        provider=provider,
        task="reason",
        options={"temperature": 0.3, "max_tokens": 200}
    )"""
content = content.replace(old_complete, new_complete, 1)

# 2. Update analyze_lyrics_sections
old_loop = """    for i, (label, text) in enumerate(sections):
        start_frame = int(i * frames_per_section)
        end_frame = int((i + 1) * frames_per_section) if i < n - 1 else total_frames - 1
        
        try:
            params = _query_llm(label, text)
            c1 = _parse_color_any(params.get("u_baseColor1")) or DEFAULT_C1
            c2 = _parse_color_any(params.get("u_baseColor2")) or DEFAULT_C2
            spd = float(params.get("speed_multiplier", DEFAULT_SPD))
            trb = float(params.get("turbulence", DEFAULT_TRB))
            engine = params.get("engine", DEFAULT_ENG)
            pose = int(params.get("pose", DEFAULT_POSE))
            custom_scene_prompt = params.get("custom_scene_prompt", "")
            log.info(f"[V13 Director] '{label}': {engine}(pose={pose}) C1={c1} spd={spd:.2f}")
        except Exception as e:
            log.warning(f"[V13 Director] Error en '{label}': {e}")
            c1, c2, spd, trb, engine, pose = DEFAULT_C1, DEFAULT_C2, DEFAULT_SPD, DEFAULT_TRB, DEFAULT_ENG, DEFAULT_POSE
            custom_scene_prompt = ""

        # Añadir al timeline narrativo
        scene = {
            "start": start_frame,
            "end": end_frame,
            "engine": engine,
            "pose": pose,
            "custom_scene_prompt": custom_scene_prompt
        }
        
        # Calcular crossfades con la escena anterior
        if i > 0:
            timeline[i-1]["transition_start"] = timeline[i-1]["end"] - crossfade_frames
            scene["incoming_end"] = scene["start"] + crossfade_frames
            
        timeline.append(scene)

        mid_frame = int(start_frame + (end_frame - start_frame) / 2)
        keyframe_frames.append(mid_frame)
        keyframes_c1.append(c1)
        keyframes_c2.append(c2)
        keyframes_spd.append(spd)
        keyframes_trb.append(trb)"""

new_loop = """    import concurrent.futures
    from core import provider_manager
    
    # Get all healthy providers for Swarm Round-Robin
    all_results = provider_manager.scan_all()
    healthy_providers = []
    for r in all_results:
        if r.is_healthy and r.models:
            healthy_providers.append((r.name, r.active_model or r.models[0]["name"]))
            
    if not healthy_providers:
        log.warning("[V13 Director Swarm] No hay proveedores IA saludables. Se usaran defaults.")
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
        futures = [executor.submit(process_section, i, label, text) for i, (label, text) in enumerate(sections)]
        for fut in concurrent.futures.as_completed(futures):
            results_unsorted.append(fut.result())
            
    results_sorted = sorted(results_unsorted, key=lambda x: x[0])

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
        log.info(f"[V13 Director Swarm] '{label}' [Brain: {prov_name} / {mod}]: {engine}(pose={pose}) C1={c1} spd={spd:.2f}")

        # Añadir al timeline narrativo
        scene = {
            "start": start_frame,
            "end": end_frame,
            "engine": engine,
            "pose": pose,
            "custom_scene_prompt": custom_scene_prompt
        }
        
        # Calcular crossfades con la escena anterior
        if i > 0:
            timeline[i-1]["transition_start"] = timeline[i-1]["end"] - crossfade_frames
            scene["incoming_end"] = scene["start"] + crossfade_frames
            
        timeline.append(scene)

        mid_frame = int(start_frame + (end_frame - start_frame) / 2)
        keyframe_frames.append(mid_frame)
        keyframes_c1.append(c1)
        keyframes_c2.append(c2)
        keyframes_spd.append(spd)
        keyframes_trb.append(trb)"""

if "import concurrent.futures" not in content:
    content = content.replace(old_loop, new_loop, 1)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)
print("Director Swarm Patch applied successfully.")
