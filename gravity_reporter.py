#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
GRAVITY AI - REPORTERO AUTÓNOMO DE LA ZONA ÁGORA V16.0 PRO
Investigación web profunda, redacción periodística profesional basada en lore,
y sincronización / publicación automática en el portal de noticias de Netlify.
"""

import os
import sys
import json
import re
import random
import subprocess
from datetime import datetime
from typing import List, Dict, Any, Tuple

# Forzar codificación UTF-8
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Configurar rutas para importar desde el Bridge
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from core import provider_manager
from core.config_manager import config
from tools.web_search import WebSearch

PORTAL_DIR = "f:\\gravity-news-portal"
NEWS_JSON_PATH = os.path.join(PORTAL_DIR, "src", "data", "news.json")

# Temas de investigación por defecto
DEFAULT_QUERIES = [
    "CBDC control biometric digital identification surveillance",
    "biometric database smart contract forced state registration",
    "AI algorithm platform censorship freedom of speech limits",
    "decentralized quantum mesh network cryptography local ágora",
    "cashless society surveillance economic block smart contract risk",
    "neuro-link brain computer interface biometric contract tracking",
    "digital sovereignty sovereign individual Stirner Ostrom DAO"
]

CATEGORY_IMAGE_MAP = {
    "Control Biométrico": "https://picsum.photos/seed/biometric/800/600",
    "Resistencia Digital": "https://picsum.photos/seed/resistance/800/600",
    "Soberanía Criptográfica": "https://picsum.photos/seed/crypto/800/600",
    "Vigilancia del Leviatán": "https://picsum.photos/seed/surveillance/800/600",
    "Tecnología Descentralizada": "https://picsum.photos/seed/decentralized/800/600",
    "default": "https://picsum.photos/seed/default/800/600"
}

def clean_llm_response(text: str) -> str:
    """Elimina etiquetas de razonamiento <think> y marcas de bloques markdown JSON."""
    # Eliminar bloques <think>
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    
    # Extraer el bloque JSON puro si está envuelto en marcas de markdown ```json
    json_match = re.search(r'```json\s*(.*?)\s*```', text, re.DOTALL)
    if json_match:
        return json_match.group(1).strip()
        
    json_match_generic = re.search(r'```\s*(.*?)\s*```', text, re.DOTALL)
    if json_match_generic:
        return json_match_generic.group(1).strip()
        
    # Buscar el primer '{' y el último '}' si no se encontraron bloques markdown
    brace_match = re.search(r'(\{.*\})', text, re.DOTALL)
    if brace_match:
        return brace_match.group(1).strip()
        
    return text.strip()

def slugify(text: str) -> str:
    """Genera un slug de URL a partir de un título."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text.strip('-')

def run_investigation(topic: str = None) -> Tuple[bool, str]:
    """Realiza la búsqueda de noticias reales en DuckDuckGo."""
    query = topic if topic else random.choice(DEFAULT_QUERIES)
    print(f"[*] Buscando información sobre: '{query}'...")
    
    search_tool = WebSearch()
    res = search_tool.execute(query=query)
    
    if not res.success:
        return False, f"Error en búsqueda web: {res.stderr}"
    
    return True, res.stdout

def write_article(search_results: str, prompt_override: str = None) -> Dict[str, Any]:
    """Usa el LLM de Gravity para redactar la noticia basada en los libros de lore y el contexto web."""
    print("[*] Iniciando motor cognitivo para redacción del artículo...")
    
    # 1. Intentar obtener el proveedor configurado por defecto o bloqueado
    provider_manager.scan_all()
    best_p, best_m = provider_manager.get_best()
    
    system_prompt = (
        "Eres Gravity, un reportero de investigación profesional, cínico y brillante de los bajos fondos de la 'Zona Ágora'. "
        "Tu misión es analizar eventos reales contemporáneos (obtenidos en los resultados de búsqueda web) a través de la lente filosófica "
        "y distópica de los libros que has escrito en este ecosistema: 'Cenizas del Leviatán' (la lucha contra el Macro-Leviatán y sus Contratos Biométricos) "
        "y 'La Física del Poder' (la extracción del trabajo cognitivo de los individuos para mantener el Lattice social).\n\n"
        "Debes redactar un reporte periodístico en ESPAÑOL, serio, riguroso, y sumamente profesional, evitando disculpas y formalidades.\n"
        "Asocia el evento de actualidad con el avance silencioso del 'Macro-Leviatán' (control estatal/corporativo) o con focos de resistencia autónoma descentralizada (Zona Ágora, Protocolo Ostrom, DAOs físicas).\n\n"
        "Es crítico que devuelvas ÚNICAMENTE un objeto JSON bien estructurado. No agregues texto antes ni después del JSON. El formato debe ser exactamente este:\n"
        "{\n"
        "  \"category\": \"Una de estas: 'Control Biométrico', 'Resistencia Digital', 'Soberanía Criptográfica', 'Vigilancia del Leviatán', 'Tecnología Descentralizada'\",\n"
        "  \"title\": \"Título impactante del reporte periodístico\",\n"
        "  \"excerpt\": \"Un resumen breve y persuasivo de 2-3 líneas sobre el reporte\",\n"
        "  \"fullText\": \"Contenido detallado en formato HTML/Markdown completo. Usa subsecciones ### para estructurarlo y dale un tono periodístico profundo, revelador y analítico. Incluye citas ficticias de Kaelen 'Ego' o analogías con el Protocolo Ostrom si es oportuno.\",\n"
        "  \"featured\": true\n"
        "}"
    )
    
    user_prompt = f"Aquí están los resultados de la búsqueda web de hoy:\n\n{search_results}\n\n"
    if prompt_override:
        user_prompt += f"Enfoque solicitado para este artículo: {prompt_override}\n\n"
    user_prompt += "Genera el JSON con el artículo periodístico ahora."

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]
    
    opts = {"temperature": 0.5, "max_tokens": 4000}
    response_raw = ""
    
    # Intentar con el mejor proveedor recomendado
    if best_p:
        try:
            print(f"[*] Intentando con proveedor principal: {best_p.name} | Modelo: {best_m}")
            response_raw = provider_manager.complete(messages=messages, model=best_m, provider=best_p.name, options=opts)
        except Exception as e:
            print(f"[!] Fallo con el proveedor principal {best_p.name}: {e}")
            response_raw = ""
            
    # Fallback si falló el principal
    if not response_raw:
        print("[*] Buscando proveedores alternativos en línea...")
        scans = provider_manager.scan_all(force=True)
        healthy_providers = [s for s in scans if s.is_healthy and s.models and s.name != (best_p.name if best_p else "")]
        
        if not healthy_providers:
            # Si LM Studio está activo y no se escaneó por force, usarlo directamente
            # (LM Studio suele retornar is_healthy True si responde)
            lm_studio = next((s for s in scans if s.name == "LM Studio" and s.is_healthy), None)
            if lm_studio:
                healthy_providers = [lm_studio]
                
        if healthy_providers:
            alt_p = healthy_providers[0]
            alt_m = alt_p.active_model or alt_p.models[0]["name"]
            print(f"[+] Proveedor alternativo encontrado: {alt_p.name} | Modelo: {alt_m}")
            try:
                response_raw = provider_manager.complete(messages=messages, model=alt_m, provider=alt_p.name, options=opts)
            except Exception as e2:
                print(f"[!] Fallo también con el proveedor alternativo {alt_p.name}: {e2}")
        else:
            print("[!] No hay más proveedores en línea para fallback.")

    if not response_raw:
        raise RuntimeError("Todos los motores de IA fallaron al procesar la redacción.")

    clean_resp = clean_llm_response(response_raw)
    try:
        article_data = json.loads(clean_resp)
    except Exception as e:
        print(f"[!] Error parseando JSON directo: {e}. Respuesta cruda:")
        print(response_raw)
        # Buscar el JSON con regex como última oportunidad
        json_match = re.search(r'(\{[\s\S]*\})', clean_resp)
        if json_match:
            try:
                article_data = json.loads(json_match.group(1))
            except Exception:
                raise RuntimeError("El modelo no devolvió un JSON estructurado válido.")
        else:
            raise RuntimeError("El modelo no devolvió un JSON estructurado válido.")
        
    # Normalizar llaves
    normalized = {}
    for k, v in article_data.items():
        k_lower = k.lower()
        if k_lower in ("title", "titulo", "título", "title_articulo"):
            normalized["title"] = v
        elif k_lower in ("excerpt", "extracto", "resumen", "description", "excerpt_articulo"):
            normalized["excerpt"] = v
        elif k_lower in ("fulltext", "fulltext_articulo", "texto", "contenido", "full_text"):
            normalized["fullText"] = v
        elif k_lower in ("category", "categoria", "categoría"):
            normalized["category"] = v
        elif k_lower in ("featured", "destacado"):
            if isinstance(v, str):
                normalized["featured"] = v.lower() in ("true", "1", "si", "sí")
            else:
                normalized["featured"] = bool(v)
        else:
            normalized[k] = v
            
    # Garantizar llaves mínimas
    if "title" not in normalized:
        normalized["title"] = "Transmisión Clandestina de la Zona Ágora"
    if "excerpt" not in normalized:
        normalized["excerpt"] = "Reporte interceptado de los nodos de Gravity AI en el subsuelo."
    if "fullText" not in normalized:
        normalized["fullText"] = "### Canal de contingencia activo\n\nNo se pudo decodificar el contenido completo."
    if "category" not in normalized:
        normalized["category"] = "Tecnología Descentralizada"
    if "featured" not in normalized:
        normalized["featured"] = False

    category = normalized["category"]
    if category not in CATEGORY_IMAGE_MAP:
        category = "Tecnología Descentralizada"
        
    normalized["id"] = slugify(normalized["title"])
    normalized["category"] = category
    normalized["date"] = datetime.now().strftime("%Y-%m-%d")
    normalized["image"] = CATEGORY_IMAGE_MAP.get(category, CATEGORY_IMAGE_MAP["default"])
    
    return normalized

def update_news_json(new_article: Dict[str, Any]):
    """Inserta el nuevo artículo al principio del catálogo en news.json."""
    if not os.path.exists(NEWS_JSON_PATH):
        # Asegurar directorio
        os.makedirs(os.path.dirname(NEWS_JSON_PATH), exist_ok=True)
        news_list = []
    else:
        try:
            with open(NEWS_JSON_PATH, "r", encoding="utf-8") as f:
                news_list = json.load(f)
                if not isinstance(news_list, list):
                    news_list = []
        except Exception:
            news_list = []
            
    # Validar duplicado por ID
    news_list = [art for art in news_list if art.get("id") != new_article["id"]]
    
    # Insertar al inicio
    news_list.insert(0, new_article)
    
    # Mantener máximo 15 noticias para rendimiento
    news_list = news_list[:15]
    
    # Guardar
    with open(NEWS_JSON_PATH, "w", encoding="utf-8") as f:
        json.dump(news_list, f, indent=2, ensure_ascii=False)
    print(f"[+] Artículo '{new_article.get('title', 'Sin Título')}' agregado con éxito a news.json")

def publish_changes():
    """Ejecuta sincronización de libros locales y publica en Netlify mediante git push."""
    print("[*] Sincronizando biblioteca física local...")
    sync_script = os.path.join(PORTAL_DIR, "sync_books.js")
    
    try:
        # Sincronizar libros primero
        subprocess.run(["node", sync_script], cwd=PORTAL_DIR, check=True)
        print("[green]✓ Biblioteca sincronizada con éxito.[/]")
    except Exception as e:
        print(f"[!] Error ejecutando sync_books.js: {e}")
        
    print("[*] Preparando publicación en GitHub para despliegue automático en Netlify...")
    try:
        # Git Status check
        subprocess.run(["git", "status"], cwd=PORTAL_DIR, check=True)
        
        # Git Add
        subprocess.run(["git", "add", "."], cwd=PORTAL_DIR, check=True)
        
        # Git Commit
        commit_msg = f"Gravity Reporter: reporte de investigación autónomo [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=PORTAL_DIR, check=True)
        
        # Git Push
        subprocess.run(["git", "push", "origin", "main"], cwd=PORTAL_DIR, check=True)
        print("[green]✓ Publicación exitosa. Netlify se actualizará en segundos.[/]")
    except subprocess.CalledProcessError as e:
        print(f"[!] Error ejecutando comandos de Git: {e}. Asegúrate de que las credenciales estén configuradas en Git global.")
    except Exception as e:
        print(f"[!] Error inesperado al publicar: {e}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Gravity AI - Reportero Autónomo")
    parser.add_argument("--topic", type=str, default=None, help="Tema de investigación específico")
    parser.add_argument("--focus", type=str, default=None, help="Enfoque particular de redacción")
    args = parser.parse_args()
    
    print("======================================================================")
    print(f"  Gravity AI Reporter V16.0 PRO - Ejecución: {datetime.now().isoformat()}")
    print("======================================================================")
    
    # 1. Investigar
    success, search_results = run_investigation(args.topic)
    if not success:
        print(f"[!] {search_results}")
        sys.exit(1)
        
    # 2. Redactar
    try:
        article = write_article(search_results, args.focus)
    except Exception as e:
        print(f"[!] Error de redacción por IA: {e}")
        sys.exit(1)
        
    # 3. Guardar en portal
    update_news_json(article)
    
    # 4. Sincronizar y publicar en Netlify
    publish_changes()
    
    print("[*] Proceso completado exitosamente.")

if __name__ == "__main__":
    main()
