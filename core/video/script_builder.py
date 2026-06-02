import os
import re
import json
from core.logger import log

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CINEMA_STYLES: dict[str, dict] = {
    "documental": {
        "label":  "Documental",
        "prefix": "Cinematic documentary, photorealistic, professional lighting, 16:9 landscape, dramatic composition, high detail, award-winning photography",
        "negative": "cartoon, anime, painting, sketch, low quality, blurry",
    },
    "anime": {
        "label":  "Anime",
        "prefix": "Anime style, vibrant colors, high-quality illustration, detailed cel shading, dynamic scene, 16:9 aspect",
        "negative": "photorealistic, 3D render, low quality, blurry, ugly",
    },
    "epico": {
        "label":  "Épico / Fantasy",
        "prefix": "Epic fantasy artwork, dramatic lighting, cinematic atmosphere, detailed digital painting, heroic composition, 16:9",
        "negative": "modern, mundane, low quality, stock photo",
    },
    "noir": {
        "label":  "Noir / Thriller",
        "prefix": "Film noir, high contrast black and white, moody shadows, 1940s aesthetic, dramatic chiaroscuro, cinematic still, 16:9",
        "negative": "colorful, bright, cheerful, low quality",
    },
    "infantil": {
        "label":  "Infantil / Cuento",
        "prefix": "Children's storybook illustration, cute and colorful, soft warm lighting, friendly characters, Pixar-style, 16:9",
        "negative": "dark, scary, violent, photorealistic, gore",
    },
    "naturaleza": {
        "label":  "Naturaleza / Wildlife",
        "prefix": "National Geographic photography, ultra high resolution, dramatic natural lighting, pristine nature, macro or wide landscape, 16:9",
        "negative": "people, buildings, urban, low quality",
    },
    "cyberpunk": {
        "label":  "Cyberpunk / Sci-Fi",
        "prefix": "Cyberpunk cityscape, neon lights, rain-soaked streets, futuristic dystopia, cinematic composition, ultra-detailed, 16:9",
        "negative": "medieval, nature, low quality, blurry",
    },
    "historico": {
        "label":  "Histórico / Épocas",
        "prefix": "Historical epic scene, period-accurate set design, dramatic oil painting style, cinematic lighting, 16:9",
        "negative": "modern, sci-fi, cartoon, low quality",
    },
    "lofi": {
        "label":  "Lo-Fi / Estudiantil",
        "prefix": "Lofi aesthetic, cozy study room, warm pastel colors, rain window, soft grain texture, illustration style, calm atmosphere, 16:9",
        "negative": "dark, scary, violent, photorealistic, high contrast, gore",
    },
    "retro80s": {
        "label":  "Retro 80s / Synth-wave",
        "prefix": "Synthwave retro 1980s aesthetic, neon pink and purple gradients, grid horizon, chrome lettering, vaporwave sunset, cinematic 16:9",
        "negative": "modern minimal, flat design, photography, low quality, blurry",
    },
    "publicitario": {
        "label":  "Publicidad / Comercial",
        "prefix": "High-end commercial photography, ultra sharp, vivid studio lighting, 4k resolution, bright and energetic, modern product advertising, 16:9",
        "negative": "dark, gloomy, low quality, amateur, blurry, messy",
    },
    "biomechanic_v13": {
        "label":  "Biomecánica V13 (Audio-Reativo)",
        "prefix": "GLSL Biomechanic Shader, audio-reactive kinematics, procedural generation",
        "negative": "static, rigid, low quality",
    },
}
DEFAULT_STYLE = "documental"

def _extract_visual_anchor(topic: str) -> str:
    """
    Usa el LLM para extraer un descriptor visual conciso y consistente del tema.
    """
    system_prompt = (
        "You are an expert visual director and prompt engineer for AI image generation. "
        "Respond ONLY with a single compact English phrase. No bullet points, no JSON."
    )
    user_prompt = (
        f"Given the story/documentary/ad topic or web content: '{topic}'\n"
        "Extract a VISUAL CHARACTER/SUBJECT ANCHOR — a compact description of the main "
        "subject's permanent visual attributes (e.g., specific setting, brand colors, "
        "character features, or main product). This anchor will be prepended to every scene prompt to maintain "
        "visual consistency across all generated images.\n"
        "If the input contains EXTRACTED WEB CONTENT, deduce the core product or business (e.g., 'a vibrant Mexican food stall with neon signs', 'a sleek modern tech office').\n"
        "Example for 'a siamese kitten named Jamon':\n"
        "  → 'siamese kitten with cream and dark brown fur, blue eyes, named Jamon, small and fluffy'\n"
        "Example for 'the history of Ancient Rome':\n"
        "  → 'ancient Roman setting, marble columns, toga-wearing citizens, Latin inscriptions'\n"
        "Respond ONLY with the anchor phrase, nothing else."
    )
    try:
        from core import provider_manager
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ]
        best_result, best_model = provider_manager.get_best()
        if not best_result:
            raise RuntimeError("No LLM disponible")
        anchor = provider_manager.complete(
            messages,
            model=best_model,
            provider=best_result.name,
            options={"temperature": 0.3, "max_tokens": 80},
        )
        anchor = anchor.strip().strip('"').strip("'")
        for prefix in ("anchor:", "→", "-", "*"):
            if anchor.lower().startswith(prefix):
                anchor = anchor[len(prefix):].strip()
        if len(anchor) > 10:
            log.info(f"[VideoStudio] Visual Anchor extraído: '{anchor[:80]}'")
            return anchor
    except Exception as e:
        log.warning(f"[VideoStudio] LLM anchor fallback ({e}). Usando topic como anchor.")

    return topic[:120]


def _get_scene_visual_context(image_path: str) -> str:
    """
    Extrae tags visuales de la escena N-1 para mantener consistencia visual en la escena N
    utilizando WD14 Tagger via ComfyUI.

    Usa build_img2prompt_workflow programáticamente si el archivo JSON externo no existe.
    Copia la imagen al directorio /input de ComfyUI antes de ejecutar el workflow.

    Args:
        image_path: Ruta absoluta a la imagen fuente.

    Returns:
        String con tags visuales separados por coma, o "" si ComfyUI no está disponible.
    """
    import time
    import shutil
    try:
        from _integrations.comfy_client import ComfyUIClient
        client = ComfyUIClient()
        if not client.is_online():
            return ""

        input_dir = os.path.join(BASE_DIR, "_integrations", "ComfyUI_windows_portable", "ComfyUI", "input")
        os.makedirs(input_dir, exist_ok=True)
        img_name = f"img2prompt_{os.path.basename(image_path)}"
        shutil.copy2(image_path, os.path.join(input_dir, img_name))

        # Intentar cargar el workflow desde archivo JSON; si no existe, construirlo
        workflow_path = os.path.join(BASE_DIR, "_integrations", "workflow_img2prompt.json")
        if os.path.exists(workflow_path):
            with open(workflow_path, "r", encoding="utf-8") as f:
                import json as _json
                workflow = _json.load(f)
            workflow["1"]["inputs"]["image"] = img_name
        else:
            workflow = client.build_img2prompt_workflow(image_name=img_name)

        prompt_id = client.queue_prompt(workflow)

        elapsed = 0
        while elapsed < 30:
            tags = client.extract_tags(prompt_id)
            if tags:
                try:
                    os.remove(os.path.join(input_dir, img_name))
                except Exception:
                    pass
                if len(tags) == 1 and isinstance(tags[0], str):
                    return tags[0]
                return ", ".join(tags)
            time.sleep(2)
            elapsed += 2

    except Exception as e:
        log.debug(f"[VideoStudio] Error en img2prompt (ComfyUI offline/Tagger fail): {e}")
    return ""



def _normalize_topic_for_lore(topic: str) -> str:
    """
    Normaliza un topic para búsqueda en el lore.
    """
    t = topic.lower().strip()
    t = re.sub(r"\s*(parte|part|capitulo|capítulo|episode|ep|vol|volume|\#)\s*[\divxlc]+\s*$", "", t).strip()
    return t


def _get_lore_context(topic: str, limit_chars: int = 4000) -> str:
    """
    Extrae contexto de lore EXCLUSIVO para el topic dado.
    """
    lore_path = os.path.join(BASE_DIR, "inputs", "cinematic_lore.txt")
    if not os.path.isfile(lore_path):
        return ""

    try:
        with open(lore_path, "r", encoding="utf-8") as f:
            content = f.read()

        clean_topic = _normalize_topic_for_lore(topic)
        if not clean_topic:
            return ""

        relevant_blocks: list[str] = []
        raw_blocks = content.split("=== HISTORIA:")
        for block in raw_blocks:
            block = block.strip()
            if not block:
                continue
            end_marker = block.find("===")
            if end_marker == -1:
                header_raw = block.split("\n")[0]
                body = block
            else:
                header_raw = block[:end_marker].strip()
                body = block[end_marker + 3:].strip()

            header_norm = _normalize_topic_for_lore(header_raw)

            if not header_norm or len(header_norm) < 4:
                continue

            match = False
            if clean_topic == header_norm:
                match = True
            elif len(clean_topic) >= 5 and len(header_norm) >= 5:
                if clean_topic in header_norm or header_norm in clean_topic:
                    match = True

            if match:
                relevant_blocks.append(
                    f"=== HISTORIA: {header_raw} ===\n{body}"
                )

        if relevant_blocks:
            context = "\n\n".join(relevant_blocks)
            log.info(
                f"[VideoStudio] Lore: {len(relevant_blocks)} bloque(s) encontrado(s) para '{topic}' "
                f"({len(context)} chars)"
            )
            return context[-limit_chars:]

        log.info(f"[VideoStudio] Lore: sin historia previa para '{topic}'. Inicio de nueva historia.")
        return ""

    except Exception as e:
        log.warning(f"[VideoStudio] Error leyendo lore: {e}")
        return ""


def _generate_script(topic: str, n_scenes: int, style: str, narration_lang: str, use_lore: bool = True) -> tuple[list[dict], str, str]:
    """
    Genera guión estructurado incorporando contexto de lore previo y un título global.
    """
    original_topic = topic
    urls = re.findall(r'(https?://\S+)', topic)
    scraped_successfully = False
    
    if urls:
        try:
            from core.firecrawl_scraper import scrape_url
            for url in urls[:1]:
                if "youtube.com" in url or "youtu.be" in url:
                    log.info("[VideoStudio] URL de YouTube detectada. Obteniendo título oficial vía oEmbed para enlazar lore...")
                    try:
                        import requests
                        oembed_url = f"https://www.youtube.com/oembed?url={url}&format=json"
                        res = requests.get(oembed_url, timeout=5)
                        if res.status_code == 200:
                            yt_data = res.json()
                            yt_title = yt_data.get("title", "")
                            if yt_title:
                                topic = topic.replace(url, f"{yt_title}")
                                original_topic = topic
                                log.info(f"[VideoStudio] Título de YouTube recuperado: '{yt_title}'")
                    except Exception as yt_e:
                        log.warning(f"[VideoStudio] Error obteniendo oEmbed de YouTube: {yt_e}")
                    break
                    
                log.info(f"[VideoStudio] URL detectada en topic. Raspando: {url}")
                api_key = ""
                try:
                    import yaml
                    with open(os.path.join(BASE_DIR, "config.yaml"), "r", encoding="utf-8") as f:
                        cfg = yaml.safe_load(f) or {}
                        api_key = cfg.get("firecrawl_api_key", "")
                except Exception as _cfg_e:
                    log.debug(f"[VideoStudio] No se pudo leer firecrawl_api_key: {_cfg_e}")
                
                scrape_res = scrape_url(url, api_key=api_key)
                if scrape_res.get("ok"):
                    scraped_text = scrape_res.get("content", "")[:4000]
                    topic = topic.replace(url, f"[{url} - CONTENIDO WEB EXTRAÍDO:\n{scraped_text}\n]")
                    log.info("[VideoStudio] URL Raspada e inyectada con éxito en el guion.")
                    scraped_successfully = True
        except Exception as e:
            log.warning(f"[VideoStudio] Error raspando URL: {e}")
            
    if not scraped_successfully:
        try:
            from core.web_search import search_and_scrape
            log.info(f"[VideoStudio] Investigando en internet sobre: '{original_topic[:50]}' para nutrir el guion...")
            knowledge = search_and_scrape(original_topic, max_results=2)
            if knowledge:
                topic = f"{topic}\n\n[CONOCIMIENTO OBTENIDO DE INTERNET PARA CONTEXTO Y PRECISIÓN:\n{knowledge}\n]"
                log.info("[VideoStudio] Conocimiento inyectado exitosamente en el guion.")
        except Exception as e:
            log.warning(f"[VideoStudio] Error en auto-investigación web: {e}")

        try:
            from core.market_researcher import analyze_competitors
            competitor_brief = analyze_competitors(original_topic)
            if competitor_brief:
                topic = f"{topic}{competitor_brief}"
        except Exception as e:
            log.warning(f"[VideoStudio] Error en análisis de mercado: {e}")

    style_info     = CINEMA_STYLES.get(style, CINEMA_STYLES[DEFAULT_STYLE])
    style_prefix   = style_info["prefix"]
    
    lore_context = ""
    if use_lore:
        lore_context = _get_lore_context(original_topic)
        if lore_context:
            log.info(f"[VideoStudio] Contexto de Lore recuperado ({len(lore_context)} chars)")

    lang_names = {
        "es": "español", "en": "English", "pt": "português",
        "fr": "français", "de": "Deutsch", "it": "italiano",
    }
    lang_label = lang_names.get(narration_lang, "español")

    system_prompt = (
        "Eres un director creativo y guionista profesional de cine, documentales y publicidad. "
        "Tu objetivo es crear narrativas visuales y auditivas que cautiven al espectador. "
        "Responde ÚNICAMENTE con JSON válido, sin texto adicional."
    )
    
    user_prompt = (
        f"Crea un guión de {n_scenes} escenas para un video sobre el siguiente tema o contenido: '{topic}'.\n"
        "Si detectas CONOCIMIENTO OBTENIDO DE INTERNET, compórtate como un investigador experto: utiliza la "
        "información factual, datos precisos y contexto proporcionado para hacer que el guion sea "
        "veraz, rico en detalles y sumamente informativo sin perder el tono narrativo.\n"
        "Si detectas CONTENIDO WEB EXTRAÍDO (por URL directa), compórtate como un experto publicista: analiza "
        "los servicios, productos o menú ofrecidos y diseña un guión altamente persuasivo.\n"
        f"Estilo visual: {style_info['label']} — {style_prefix}\n"
        f"Idioma de narración: {lang_label}\n\n"
    )

    if lore_context:
        user_prompt += (
            "CONTEXTO DE HISTORIAS PREVIAS (Lore):\n"
            "Utiliza esta información para mantener coherencia si este video es una continuación "
            "o parte de un universo ya existente:\n"
            f"{lore_context}\n\n"
        )

    user_prompt += (
        "REGLA CRÍTICA DE CONSISTENCIA VISUAL: El campo 'image_prompt' de CADA escena "
        "DEBE comenzar describiendo al personaje/sujeto principal con los MISMOS atributos visuales "
        "(raza, color, rasgos físicos, nombre) en todas las escenas. Nunca omitas estos atributos.\n\n"
        "REGLA CRÍTICA DE NARRACIÓN: El campo 'narration' DEBE contener ÚNICAMENTE lo que dirá el "
        "locutor en voz en off. DEBE ser una historia fluida o un texto publicitario atrapante. "
        "PROHIBIDO incluir metadatos como 'Escena 1', 'Imagen:', 'Título:', o direcciones de cámara. "
        "Solo el diálogo hablado puro y continuo.\n\n"
        "Responde con este JSON exacto (sin ningún texto antes o después):\n"
        "{\n"
        '  "video_title": "Un título global creativo, comercial y atractivo para todo el video",\n'
        '  "scenes": [\n'
        "    {\n"
        '      "title": "Título de escena MUY CORTO",\n'
        '      "character_anchor": "Descripción compacta en inglés del sujeto principal con atributos físicos fijos",\n'
        '      "image_prompt": "Descripción visual detallada en inglés. DEBE incluir el character_anchor al inicio.",\n'
        f'      "narration": "Texto de narración en {lang_label} para esta escena (2-4 oraciones)."\n'
        "    }\n"
        "  ]\n"
        "}\n"
        f"Genera exactamente {n_scenes} escenas dentro del array 'scenes'. Solo JSON, nada más."
    )

    try:
        from core import provider_manager
        from core.multi_agent import PipelineStep, run_pipeline
        import yaml
        
        writer_prov, writer_mod = None, None
        audit_prov, audit_mod = None, None
        
        try:
            with open(os.path.join(BASE_DIR, "config.yaml"), "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}
                ar = cfg.get("agent_routing", {})
                if ar.get("coder"):
                    writer_prov = ar["coder"].get("provider")
                    writer_mod = ar["coder"].get("model")
                if ar.get("auditor"):
                    audit_prov = ar["auditor"].get("provider")
                    audit_mod = ar["auditor"].get("model")
        except Exception:
            pass
            
        best_result, best_model = provider_manager.get_best()
        if not best_result:
            raise RuntimeError("No hay proveedor LLM activo")
            
        writer_prov = writer_prov or best_result.name
        writer_mod = writer_mod if writer_mod and writer_mod != "auto" else best_model
        
        audit_prov = audit_prov or best_result.name
        audit_mod = audit_mod if audit_mod and audit_mod != "auto" else best_model

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ]
        
        log.info(f"[VideoStudio] Iniciando pipeline Multi-Agente para el guion (Escritor: {writer_prov}, Auditor: {audit_prov})...")
        
        steps = [
            PipelineStep(provider=writer_prov, model=writer_mod),
            PipelineStep(provider=audit_prov, model=audit_mod, role="Actúa como un Auditor Experto en Retención de Audiencia. Revisa el JSON anterior. Mejora los ganchos emocionales de la narración en los primeros 5 segundos. Asegúrate de que los image_prompts sean extremadamente cinemáticos y consistentes. Devuelve ÚNICAMENTE EL JSON CORREGIDO, sin explicaciones ni markdown text. Solo JSON puro.")
        ]
        
        content = run_pipeline(steps=steps, initial_messages=messages, options={"temperature": 0.7})

        content = content.strip()
        if content.startswith("```"):
            parts = content.split("```")
            content = parts[1] if len(parts) > 1 else parts[0]
            if content.startswith("json"): content = content[4:]
        content = content.strip()

        start = content.find("{")
        end   = content.rfind("}") + 1
        if start != -1 and end > start:
            content = content[start:end]

        data = json.loads(content)
        scenes = data.get("scenes", [])
        generated_title = data.get("video_title", original_topic[:60])
        
        if isinstance(scenes, list) and len(scenes) > 0:
            anchor = ""
            for sc in scenes:
                ca = sc.get("character_anchor", "").strip()
                if ca and len(ca) > 5:
                    anchor = ca
                    break
            if not anchor:
                anchor = _extract_visual_anchor(topic)
            return scenes[:n_scenes], anchor, generated_title

        raise ValueError("LLM no devolvió lista JSON válida en 'scenes'")

    except Exception as e:
        log.warning(f"[VideoStudio] LLM no disponible ({e}). Fallback con escenas genéricas.")

    anchor = topic[:120]
    _fallback_narrations = [
        f"En este fascinante recorrido por {original_topic[:60]}, descubriremos aspectos que transformarán tu perspectiva sobre el mundo.",
        f"El tema de {original_topic[:60]} esconde secretos que pocos conocen. Prepárate para una exploración profunda y reveladora.",
        f"Cada detalle de {original_topic[:60]} nos acerca más a comprender fenómenos que moldean nuestra realidad cotidiana.",
        f"La historia detrás de {original_topic[:60]} es más extraordinaria de lo que imaginas. Acompáñanos en este viaje único.",
        f"Analizamos en detalle {original_topic[:60]} con datos precisos y perspectivas que cambiarán tu forma de ver este tema.",
        f"Concluimos nuestra exploración de {original_topic[:60]} con las conclusiones más importantes y lo que significa para el futuro.",
    ]
    style_info = CINEMA_STYLES.get(style, CINEMA_STYLES[DEFAULT_STYLE])
    style_prefix = style_info["prefix"]
    scenes = [
        {
            "title":            f"Capítulo {i+1}",
            "character_anchor": anchor,
            "image_prompt":     f"{anchor}, cinematic scene {i+1}, {style_prefix}, high detail, dramatic lighting",
            "narration":        _fallback_narrations[i % len(_fallback_narrations)],
            "mood":             "neutral",
        }
        for i in range(n_scenes)
    ]
    return scenes, anchor, original_topic[:60]
