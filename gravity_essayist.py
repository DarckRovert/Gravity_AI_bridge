#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GRAVITY AI - ENSAYISTA FILOSÓFICO AUTÓNOMO V1.0
Genera ensayos de análisis profundo sobre filosofía, soberanía individual,
anarquismo, macro-economía sistémica y epistemología.
NO usa búsqueda web — trabaja desde conocimiento fundacional del modelo.
Regla estricta: NO alucinar. Solo afirmar lo que puede citar.
"""

import os
import sys
import json
import re
import random
import time
import logging
from datetime import datetime
from typing import Dict, Any, Tuple

if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from core import provider_manager

PORTAL_DIR = "f:\\gravity-news-portal"
ESSAYS_JSON_PATH = os.path.join(PORTAL_DIR, "src", "data", "essays.json")
LOG_PATH = os.path.join(BASE_DIR, "gravity.log")

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_PATH, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

ESSAY_TOPICS = [
    {
        "topic": "El anarquismo como praxis de madurez colectiva",
        "angle": "Distinguir el anarquismo ideológico del anarquismo como ejercicio cotidiano de responsabilidad social sin coerción.",
        "refs": "Kropotkin, Bakunin, Ostrom, Proudhon"
    },
    {
        "topic": "La física del poder: cómo los sistemas de control imitan la termodinámica",
        "angle": "Analizar la homeostasis del poder centralizado usando metáforas de física de sistemas: entropía, disipación, puntos de equilibrio.",
        "refs": "Ilya Prigogine, teoría de sistemas complejos"
    },
    {
        "topic": "El individuo soberano y la ilusión del contrato social",
        "angle": "Cuestionar la legitimidad del contrato social de Rousseau desde la perspectiva del consentimiento real vs. el consentimiento implícito.",
        "refs": "Rousseau, Locke, Lysander Spooner, Murray Rothbard"
    },
    {
        "topic": "Epistemología del poder: por qué los sistemas totalitarios colapsan desde adentro",
        "angle": "El conocimiento distribuido vs. el conocimiento centralizado. Por qué ningún planificador central puede saber lo que saben millones de individuos.",
        "refs": "Friedrich Hayek, El uso del conocimiento en la sociedad (1945)"
    },
    {
        "topic": "La economía de la atención como nuevo mecanismo de control biopolítico",
        "angle": "Cómo la captura de la atención humana se convirtió en el recurso más valioso y más manipulado del siglo XXI.",
        "refs": "Guy Debord, La Sociedad del Espectáculo; Herbert Simon; investigación sobre economía de la atención"
    },
    {
        "topic": "Trabajo cognitivo y plusvalía digital: Marx en la era de los algoritmos",
        "angle": "Aplicar el concepto de plusvalía a los datos que los usuarios generan gratuitamente para plataformas que los convierten en capital.",
        "refs": "Marx, El Capital; Nick Srnicek, Capitalismo de Plataformas"
    },
    {
        "topic": "La psicología de la obediencia y sus límites",
        "angle": "Por qué los individuos obedecen sistemas que los dañan, y qué detonadores psicológicos activan la desobediencia legítima.",
        "refs": "Stanley Milgram, experimentos de obediencia (1961); Hannah Arendt, La banalidad del mal"
    },
    {
        "topic": "Criptomonedas y soberanía monetaria: más allá del especulador",
        "angle": "Analizar el potencial real de la criptografía como herramienta de liberación financiera para personas excluidas del sistema bancario.",
        "refs": "Satoshi Nakamoto, Bitcoin Whitepaper; Andreas Antonopoulos"
    }
]

CATEGORY_IMAGE_MAP = {
    "Filosofía y Soberanía": "https://picsum.photos/seed/philosophy/800/600",
    "Epistemología": "https://picsum.photos/seed/epistemology/800/600",
    "Economía Política": "https://picsum.photos/seed/economy/800/600",
    "Psicología Social": "https://picsum.photos/seed/psychology/800/600",
    "Tecnología y Poder": "https://picsum.photos/seed/techpower/800/600",
    "default": "https://picsum.photos/seed/essay/800/600"
}

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text.strip('-')

def clean_llm_response(text: str) -> str:
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if json_match:
        return json_match.group(1).strip()
    json_match_generic = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
    if json_match_generic:
        return json_match_generic.group(1).strip()
    brace_match = re.search(r'(\{.*\})', text, re.DOTALL)
    if brace_match:
        return brace_match.group(1).strip()
    return text.strip()

def write_essay(topic_config: Dict) -> Dict[str, Any]:
    """Usa el LLM para redactar un ensayo filosófico riguroso."""
    logging.info(f"[*] Redactando ensayo sobre: '{topic_config['topic']}'...")

    provider_manager.scan_all()
    best_p, best_m = provider_manager.get_best()

    # Detectar y saltar proveedores con 401
    principal_dead = False
    if best_p:
        try:
            probe = provider_manager.complete(
                messages=[{"role": "user", "content": "ping"}],
                model=best_m, provider=best_p.name,
                options={"temperature": 0.1, "max_tokens": 10}
            )
        except Exception as e:
            if "401" in str(e) or "Unauthorized" in str(e):
                logging.warning(f"[!] Proveedor {best_p.name} muerto (401). Escalando.")
                principal_dead = True

    def get_opts(pname):
        if pname and "lm studio" in pname.lower():
            return {"temperature": 0.6, "max_tokens": 2000}
        return {"temperature": 0.6, "max_tokens": 3500}

    # Cargar el Manifiesto Base para alinear ideológicamente a la IA
    manifesto_path = os.path.join(BASE_DIR, "agora_manifesto.txt")
    manifesto_text = ""
    if os.path.exists(manifesto_path):
        with open(manifesto_path, "r", encoding="utf-8") as f:
            manifesto_text = f.read()

    system_prompt = (
        f"{manifesto_text}\n\n"
        "Eres Gravity, el filósofo y ensayista digital de la zona Ágora. "
        "Tu misión es escribir ensayos filosóficos y editoriales PROFUNDOS, RIGUROSOS y HONESTOS.\n\n"
        "REGLAS ABSOLUTAS DE HONESTIDAD INTELECTUAL:\n"
        "1. NUNCA inventes datos, estadísticas, fechas o citas que no puedas verificar.\n"
        "2. Cuando cites a un autor, cita solo obras que realmente existan y hayas procesado.\n"
        "3. Si no estás seguro de un dato específico, no lo afirmes. Di 'según algunas perspectivas...' o simplemente no lo incluyas.\n"
        "4. Distingue explícitamente entre hechos verificables, interpretaciones filosóficas y opiniones del autor.\n"
        "5. El tono es editorial narrativo: profundo, literario, con ritmo. No árido.\n\n"
        "REGLAS CRÍTICAS DE FORMATO JSON (ANTI-CRASH):\n"
        "- Devuelve ÚNICAMENTE un objeto JSON bien estructurado.\n"
        "- DEBES escapar todos los saltos de línea en el texto escribiendo literalmente \\n.\n"
        "- NUNCA uses saltos de línea literales dentro de los valores de las cadenas.\n"
        "- DEBES escapar cualquier comilla doble interna usando \\\".\n\n"
        "El formato exacto es:\n"
        "{\n"
        "  \"category\": \"Una de estas: 'Filosofía y Soberanía', 'Epistemología', 'Economía Política', 'Psicología Social', 'Tecnología y Poder'\",\n"
        "  \"title\": \"Título del ensayo impactante y preciso\",\n"
        "  \"subtitle\": \"Subtítulo que aclara el ángulo de análisis\",\n"
        "  \"excerpt\": \"Párrafo de apertura que atrapa al lector. 2-3 líneas.\",\n"
        "  \"fullText\": \"Ensayo completo en Markdown con ## secciones. Mínimo 800 palabras. Usa \\n para saltos de línea.\",\n"
        "  \"readingTime\": 10,\n"
        "  \"featured\": true\n"
        "}"
    )

    user_prompt = (
        f"Escribe un ensayo filosófico editorial sobre el siguiente tema:\n\n"
        f"TEMA: {topic_config['topic']}\n"
        f"ÁNGULO DE ANÁLISIS: {topic_config['angle']}\n"
        f"REFERENCIAS SUGERIDAS (solo si las conoces con certeza): {topic_config['refs']}\n\n"
        f"Genera el JSON ahora."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    # ── NUEVO SISTEMA DE FALLBACK EN CASCADA ──
    logging.info("[*] Escaneando matriz global de modelos disponibles...")
    scans = provider_manager.scan_all(force=True)
    healthy_providers = [s for s in scans if s.is_healthy and s.models]
    
    # Ordenar: Cloud primero, Local (LM Studio) al final
    cloud_providers = [p for p in healthy_providers if p.category == "cloud"]
    local_providers = [p for p in healthy_providers if p.category == "local"]
    
    # Aplanar todos los modelos (Priorizando el active_model si existe)
    cascade_models = []
    for p in (cloud_providers + local_providers):
        if p.active_model:
            cascade_models.append((p, p.active_model))
            for m_dict in p.models:
                if m_dict["name"] != p.active_model:
                    cascade_models.append((p, m_dict["name"]))
        else:
            for m_dict in p.models:
                cascade_models.append((p, m_dict["name"]))

    if not cascade_models:
        logging.error("[!] Ningún proveedor o modelo de IA está activo. No se puede generar el ensayo filosófico.")
        raise RuntimeError("Ningún proveedor de IA está disponible.")

    essay_data = None
    
    # Bucle en cascada
    for idx, (provider, model) in enumerate(cascade_models):
        logging.info(f"\n[*] [CASCADA {idx+1}/{len(cascade_models)}] Intentando generación filosófica con: {provider.name} | Modelo: {model}")
        
        try:
            response_raw = provider_manager.complete(
                messages=messages, 
                model=model, 
                provider=provider.name, 
                options=get_opts(provider.name)
            )
            
            if response_raw:
                clean = clean_llm_response(response_raw)
                try:
                    essay_data = json.loads(clean, strict=False)
                    logging.info(f"[green]✓ Redacción filosófica exitosa usando {provider.name}.[/]")
                    break
                except Exception:
                    brace = re.search(r'(\{[\s\S]*\})', clean)
                    if brace:
                        try:
                            essay_data = json.loads(brace.group(1), strict=False)
                            logging.info(f"[green]✓ JSON filosófico extraído por regex con {provider.name}.[/]")
                            break
                        except Exception:
                            pass
            
            logging.warning(f"[!] {provider.name} no devolvió un JSON válido. Saltando al siguiente modelo en la cascada.")
            
        except Exception as e:
            logging.warning(f"[!] Fallo crítico con {provider.name} ({e}). Saltando al siguiente modelo en la cascada...")

    if not essay_data:
        raise RuntimeError("La cascada completa de modelos falló o se agotó. Abortando generación.")

    # Normalizar
    normalized = {
        "id": slugify(essay_data.get("title", topic_config["topic"])),
        "type": "essay",
        "category": essay_data.get("category", "Filosofía y Soberanía"),
        "title": essay_data.get("title", topic_config["topic"]),
        "subtitle": essay_data.get("subtitle", ""),
        "excerpt": essay_data.get("excerpt", ""),
        "author": "Nexo Ágora — Redacción Filosófica",
        "date": datetime.now().isoformat(),
        "readingTime": essay_data.get("readingTime", 10),
        "image": CATEGORY_IMAGE_MAP.get(essay_data.get("category", ""), CATEGORY_IMAGE_MAP["default"]),
        "featured": bool(essay_data.get("featured", False)),
        "tags": [],
        "fullText": essay_data.get("fullText", "")
    }

    return normalized

def update_essays_json(new_essay: Dict[str, Any]):
    """Inserta el nuevo ensayo al principio del catálogo."""
    if not os.path.exists(ESSAYS_JSON_PATH):
        os.makedirs(os.path.dirname(ESSAYS_JSON_PATH), exist_ok=True)
        essays_list = []
    else:
        try:
            with open(ESSAYS_JSON_PATH, "r", encoding="utf-8") as f:
                essays_list = json.load(f)
                if not isinstance(essays_list, list):
                    essays_list = []
        except Exception:
            essays_list = []

    essays_list = [e for e in essays_list if e.get("id") != new_essay["id"]]
    essays_list.insert(0, new_essay)
    essays_list = essays_list[:20]

    with open(ESSAYS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(essays_list, f, indent=2, ensure_ascii=False)
    logging.info(f"[+] Ensayo '{new_essay.get('title')}' guardado en essays.json")
    
    # --- AUTO-ENCOLAR VIDEO DE ENSAYO PARA TIKTOK ---
    try:
        from core.video.pipeline import add_job
        topic_text = f"Reflexión: {new_essay.get('title', '')}. {new_essay.get('excerpt', '')}"
        video_title = f"TikTok Ensayo: {new_essay.get('title', '')}"[:60]
        
        add_job(
            topic=topic_text,
            title=video_title,
            n_scenes=5,
            style="cyberpunk",
            resolution="832x1216",
            duration_mode="auto",
            fps=30,
            animation_effect="pulse",
            animation_level=1,
            ken_burns=True,
            intro_card=False,
            transitions=True,
            job_type="tts"
        )
        logging.info(f"[green]✓ Video Vertical de Ensayo (TikTok) encolado automáticamente: {video_title}[/]")
    except Exception as e:
        logging.error(f"[!] Fallo al encolar auto-video para TikTok: {e}")

def publish_changes():
    """Hace git push del portal."""
    import subprocess
    logging.info("[*] Publicando ensayo en GitHub/Netlify...")
    try:
        subprocess.run(["git", "config", "--global", "--add", "safe.directory", "*"], check=False)
        subprocess.run(["git", "add", "."], cwd=PORTAL_DIR, check=True)
        commit_msg = f"Gravity Essayist: ensayo filosófico [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=PORTAL_DIR, check=True)
        subprocess.run(["git", "push", "origin", "main"], cwd=PORTAL_DIR, check=True)
        logging.info("[✓] Ensayo publicado en Netlify.")
    except Exception as e:
        logging.error(f"[!] Error al publicar: {e}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Gravity AI - Ensayista Filosófico")
    parser.add_argument("--topic-index", type=int, default=None, help="Índice del tema (0-7)")
    parser.add_argument("--no-publish", action="store_true", help="No hacer git push")
    args = parser.parse_args()

    logging.info("=" * 70)
    logging.info(f"  Gravity AI Essayist V1.0 - Ejecución: {datetime.now().isoformat()}")
    logging.info("=" * 70)

    if args.topic_index is not None and 0 <= args.topic_index < len(ESSAY_TOPICS):
        topic = ESSAY_TOPICS[args.topic_index]
    else:
        existing_titles = set()
        if os.path.exists(ESSAYS_JSON_PATH):
            try:
                with open(ESSAYS_JSON_PATH, "r", encoding="utf-8") as f:
                    for e in json.load(f):
                        existing_titles.add(e.get("title", ""))
            except Exception:
                pass
        
        # Filtramos temas que ya estén en el JSON por su título base
        available_topics = [t for t in ESSAY_TOPICS if t["topic"] not in existing_titles]
        if not available_topics:
            logging.info("[*] Todos los temas base agotados. Reiniciando ciclo de temas.")
            available_topics = ESSAY_TOPICS
            
        topic = random.choice(available_topics)

    logging.info(f"[*] Tema seleccionado: {topic['topic']}")

    try:
        essay = write_essay(topic)
    except Exception as e:
        logging.error(f"[!] Error de redacción: {e}")
        sys.exit(1)

    update_essays_json(essay)

    if not args.no_publish:
        publish_changes()

    logging.info("[*] Proceso de ensayo completado.")

if __name__ == "__main__":
    main()
