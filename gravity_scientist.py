#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GRAVITY AI - CIENTÍFICO AUTÓNOMO V1.0
Genera artículos de divulgación científica rigurosos buscando en la web
papers recientes y hallazgos verificables. Cero alucinaciones.
Fuentes: arXiv, PubMed, Nature, Science, revistas académicas peer-reviewed.
"""

import os
import sys
import json
import re
import random
import time
import logging
import urllib.parse
import urllib.request
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
from tools.web_search import WebSearch

PORTAL_DIR = "f:\\gravity-news-portal"
SCIENCE_JSON_PATH = os.path.join(PORTAL_DIR, "src", "data", "science.json")
LOG_PATH = os.path.join(BASE_DIR, "gravity.log")

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_PATH, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

SCIENCE_QUERIES = [
    "quantum computing breakthrough 2025 site:arxiv.org OR site:nature.com",
    "neuroscience consciousness research 2025 peer reviewed",
    "CRISPR gene editing new findings 2025 site:pubmed.ncbi.nlm.nih.gov",
    "dark matter dark energy discovery 2025 site:arxiv.org",
    "artificial intelligence emergence cognition research 2025",
    "microbiome gut brain axis mental health research 2025",
    "fusion energy milestone 2025 site:nature.com OR site:science.org",
    "climate tipping points feedback loops research 2025",
    "epigenetics inheritance mechanisms research 2025 peer reviewed",
    "quantum biology photosynthesis bird navigation 2025"
]

CATEGORY_IMAGE_MAP = {
    "Física y Cosmología": "https://picsum.photos/seed/physics/800/600",
    "Neurociencia": "https://picsum.photos/seed/neuroscience/800/600",
    "Biología y Genética": "https://picsum.photos/seed/genetics/800/600",
    "Computación Cuántica": "https://picsum.photos/seed/quantum/800/600",
    "Inteligencia Artificial": "https://picsum.photos/seed/aisci/800/600",
    "Clima y Ecosistemas": "https://picsum.photos/seed/climate/800/600",
    "Medicina y Bioética": "https://picsum.photos/seed/medicine/800/600",
    "default": "https://picsum.photos/seed/science/800/600"
}

def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text.strip('-')

def clean_llm_response(text: str) -> str:
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    m = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if m:
        return m.group(1).strip()
    m = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
    if m:
        return m.group(1).strip()
    m = re.search(r'(\{.*\})', text, re.DOTALL)
    if m:
        return m.group(1).strip()
    return text.strip()

def run_search(query: str) -> str:
    logging.info(f"[*] Buscando en la web: '{query}'...")
    tool = WebSearch()
    res = tool.execute(query=query)
    if not res.success:
        logging.warning(f"[!] Error en búsqueda: {res.stderr}")
        return ""
    return res.stdout

def write_science_article(search_results: str, query: str) -> Dict[str, Any]:
    """Redacta un artículo científico de divulgación basado en resultados reales."""
    # (El escaneo global y fallback ahora se realiza en modo Cascada más abajo)



    # Cargar el Manifiesto Base para alinear ideológicamente a la IA
    manifesto_path = os.path.join(BASE_DIR, "agora_manifesto.txt")
    manifesto_text = ""
    if os.path.exists(manifesto_path):
        with open(manifesto_path, "r", encoding="utf-8") as f:
            manifesto_text = f.read()

    system_prompt = (
        f"{manifesto_text}\n\n"
        "Eres Gravity, el investigador científico y teórico de sistemas. Tu misión es explicar "
        "hallazgos científicos reales de manera clara, accesible y honesta en español.\n\n"
        "REGLAS ABSOLUTAS DE RIGOR CIENTÍFICO:\n"
        "1. SOLO afirmar lo que está documentado en los resultados de búsqueda que se te proporcionan.\n"
        "2. NUNCA inventar datos, porcentajes, nombres de investigadores o títulos de papers.\n"
        "3. Citar explícitamente las fuentes que encontraste en los resultados de búsqueda.\n"
        "4. Distinguir claramente entre: hechos confirmados, hipótesis activas, y especulación.\n"
        "5. Si los resultados no tienen suficiente información, escribir un artículo más corto y honesto.\n\n"
        "REGLAS CRÍTICAS DE FORMATO JSON (ANTI-CRASH):\n"
        "- Devuelve ÚNICAMENTE un objeto JSON.\n"
        "- Escapa los saltos de línea con \\n.\n"
        "- Escapa las comillas internas con \\\".\n\n"
        "El formato exacto es:\n"
        "{\n"
        "  \"category\": \"Una de: 'Física y Cosmología', 'Neurociencia', 'Biología y Genética', 'Computación Cuántica', 'Inteligencia Artificial', 'Clima y Ecosistemas', 'Medicina y Bioética'\",\n"
        "  \"title\": \"Título preciso y accesible del artículo científico\",\n"
        "  \"subtitle\": \"Subtítulo que sitúa el hallazgo en contexto\",\n"
        "  \"excerpt\": \"Resumen del hallazgo en 2-3 líneas claras para el público general.\",\n"
        "  \"fullText\": \"Artículo completo en Markdown con ## secciones. Cita las fuentes. Usa \\n para saltos de línea.\",\n"
        "  \"readingTime\": 8,\n"
        "  \"featured\": false\n"
        "}"
    )

    user_prompt = (
        f"Basándote en los siguientes resultados de búsqueda sobre '{query}', "
        f"redacta un artículo de divulgación científica riguroso:\n\n"
        f"{search_results}\n\n"
        f"Genera el JSON ahora. Si los resultados son escasos, escribe menos pero con honestidad total."
    )

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    # ── NUEVO SISTEMA MULTI-AGENTE (ENJAMBRE CONCURRENTE) ──
    logging.info("[*] Escaneando matriz global de modelos disponibles...")
    scans = provider_manager.scan_all(force=True)
    healthy_providers = [s for s in scans if s.is_healthy and s.models]
    
    provider_names = [p.name for p in healthy_providers]

    if not provider_names:
        logging.error("[!] Ningún proveedor de IA está activo. No se puede generar el artículo científico.")
        raise RuntimeError("Ningún proveedor de IA está disponible.")

    logging.info(f"[*] Lanzando petición en paralelo a múltiples IA: {', '.join(provider_names)}")
    
    from core.multi_agent import compare
    results = compare(
        messages=messages,
        providers=provider_names,
        n_models=len(provider_names),
        options={"temperature": 0.5, "max_tokens": 2500},
        timeout=200.0
    )
    
    article_data = None
    
    sorted_results = sorted(results, key=lambda x: x.get("elapsed", 999))
    
    for res in sorted_results:
        provider_name = res.get("provider", "Unknown")
        model = res.get("model", "Unknown")
        response_raw = res.get("response", "")
        elapsed = res.get("elapsed", 0)
        
        if not response_raw or "[Error" in response_raw or "offline" in response_raw or "[No results]" in response_raw:
            logging.warning(f"[!] {provider_name} ({model}) falló o dio error en {elapsed}s.")
            continue
            
        logging.info(f"\n[*] Evaluando respuesta científica de {provider_name} ({model}) completada en {elapsed}s")
        
        try:
            clean = clean_llm_response(response_raw)
            try:
                article_data = json.loads(clean, strict=False)
                logging.info(f"[green]✓ Redacción científica exitosa (GANADOR) usando {provider_name} en {elapsed}s.[/]")
                break
            except Exception:
                brace = re.search(r'(\{[\s\S]*\})', clean)
                if brace:
                    try:
                        article_data = json.loads(brace.group(1), strict=False)
                        logging.info(f"[green]✓ JSON científico extraído por regex (GANADOR) con {provider_name} en {elapsed}s.[/]")
                        break
                    except Exception:
                        pass
        except Exception as e:
            logging.warning(f"[!] Error al limpiar la respuesta de {provider_name}: {e}")
            continue

    if not article_data:
        raise RuntimeError("El enjambre de modelos falló o se agotó. Abortando generación.")

    # Normalizar llaves para tolerar que el LLM las traduzca al español
    translated_data = {}
    for k, v in article_data.items():
        k_lower = k.lower()
        if k_lower in ("title", "titulo", "título"):
            translated_data["title"] = v
        elif k_lower in ("subtitle", "subtitulo", "subtítulo"):
            translated_data["subtitle"] = v
        elif k_lower in ("excerpt", "extracto", "resumen"):
            translated_data["excerpt"] = v
        elif k_lower in ("fulltext", "texto", "contenido", "cuerpo"):
            translated_data["fullText"] = v
        elif k_lower in ("category", "categoria", "categoría"):
            translated_data["category"] = v
        else:
            translated_data[k] = v

    normalized = {
        "id": slugify(translated_data.get("title", query)),
        "type": "science",
        "category": translated_data.get("category", "Ciencia"),
        "title": translated_data.get("title", "Hallazgo Científico Interceptado"),
        "subtitle": translated_data.get("subtitle", ""),
        "excerpt": translated_data.get("excerpt", ""),
        "author": "Nexo Ágora — Redacción Científica",
        "date": datetime.now().isoformat(),
        "readingTime": translated_data.get("readingTime", 8),
        "featured": bool(translated_data.get("featured", False)),
        "tags": [],
        "fullText": translated_data.get("fullText", "")
    }

    title_encoded = urllib.parse.quote(normalized["title"])
    img_url = f"https://image.pollinations.ai/prompt/cyberpunk%20science%20dark%20lab%20{title_encoded}?width=800&height=600&nologo=true"
    normalized["image"] = img_url

    # Pre-calentamiento para caché en CDN
    try:
        logging.info(f"[*] Pre-calentando imagen IA científica...")
        req = urllib.request.Request(img_url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        urllib.request.urlopen(req, timeout=45)
        logging.info("[✓] Imagen IA científica lista en CDN.")
    except Exception as e:
        logging.warning(f"[!] Aviso al pre-calentar imagen: {e}")

    return normalized

def update_science_json(new_article: Dict[str, Any]):
    if not os.path.exists(SCIENCE_JSON_PATH):
        os.makedirs(os.path.dirname(SCIENCE_JSON_PATH), exist_ok=True)
        articles = []
    else:
        try:
            with open(SCIENCE_JSON_PATH, "r", encoding="utf-8") as f:
                articles = json.load(f)
                if not isinstance(articles, list):
                    articles = []
        except Exception:
            articles = []

    articles = [a for a in articles if a.get("id") != new_article["id"]]
    articles.insert(0, new_article)
    articles = articles[:20]

    with open(SCIENCE_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(articles, f, indent=2, ensure_ascii=False)
    logging.info(f"[+] Artículo '{new_article.get('title')}' guardado en science.json")
    
    # --- AUTO-ENCOLAR VIDEO CIENTÍFICO DE TIKTOK ---
    try:
        from core.video.pipeline import add_job
        topic_text = f"Sabías que: {new_article.get('title', '')}. {new_article.get('excerpt', '')}"
        video_title = f"TikTok Science: {new_article.get('title', '')}"[:60]
        
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
        logging.info(f"[green]✓ Video Vertical Científico (TikTok) encolado automáticamente: {video_title}[/]")
    except Exception as e:
        logging.error(f"[!] Fallo al encolar auto-video para TikTok: {e}")

def publish_changes():
    import subprocess
    logging.info("[*] Publicando investigación en GitHub/Netlify...")
    try:
        subprocess.run(["git", "config", "--global", "--add", "safe.directory", "*"], check=False)
        subprocess.run(["git", "add", "."], cwd=PORTAL_DIR, check=True)
        commit_msg = f"Gravity Scientist: artículo científico [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"
        # check=False para no crashear si no hay cambios que commitear
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=PORTAL_DIR, check=False)
        
        env = os.environ.copy()
        env["GIT_TERMINAL_PROMPT"] = "0"
        
        push_res = subprocess.run(["git", "push", "origin", "HEAD"], cwd=PORTAL_DIR, env=env, check=False, capture_output=True, text=True)
        if push_res.returncode == 0:
            logging.info("[✓] Artículo publicado en Netlify.")
        else:
            logging.error(f"[!] Error al publicar en Netlify (Push fallido): {push_res.stderr.strip()}")
    except Exception as e:
        logging.error(f"[!] Error al publicar: {e}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Gravity AI - Científico Autónomo")
    parser.add_argument("--query", type=str, default=None, help="Query de búsqueda específica")
    parser.add_argument("--no-publish", action="store_true", help="No hacer git push")
    args = parser.parse_args()

    logging.info("=" * 70)
    logging.info(f"  Gravity AI Scientist V1.0 - Ejecución: {datetime.now().isoformat()}")
    logging.info("=" * 70)

    query = args.query if args.query else random.choice(SCIENCE_QUERIES)
    logging.info(f"[*] Query: {query}")

    search_results = run_search(query)
    if not search_results:
        logging.error("[!] Sin resultados de búsqueda. Abortando.")
        sys.exit(1)

    try:
        article = write_science_article(search_results, query)
    except Exception as e:
        logging.error(f"[!] Error de redacción: {e}")
        sys.exit(1)

    update_science_json(article)

    if not args.no_publish:
        publish_changes()

    logging.info("[*] Proceso científico completado.")

if __name__ == "__main__":
    main()
