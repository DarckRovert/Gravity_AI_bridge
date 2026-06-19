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
import time
import subprocess
import logging
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
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
LOG_PATH = os.path.join(BASE_DIR, "gravity.log")

# Configurar Logging Táctico
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_PATH, encoding='utf-8'),
        logging.StreamHandler(sys.stdout)
    ]
)

# Temas de investigación por defecto centrados en geopolítica y Perú
DEFAULT_QUERIES = [
    "Peru political crisis geopolitical control resource extraction international",
    "Peru digital surveillance biometric identification protests control",
    "Latin america Peru macro-economics algorithmic control hidden agenda",
    "CBDC control biometric digital identification surveillance global economy",
    "decentralized mesh network cryptography local ágora latin america",
    "digital sovereignty sovereign individual State control Latin America",
    "international intelligence operations algorithms political control Peru",
    "global medicine bioethics pharmaceutical control genetic surveillance",
    "cultural engineering social conditioning psychology mass media cinema",
    "sports analytics biometric tracking population control entertainment distraction",
    "advanced science quantum computing artificial intelligence anomalies",
    "global religion belief systems ideological control mass psychology",
    "Peru abuso policial crimen de estado comisaría encubrimiento",
    "brutalidad policial estado represivo encubrimiento legal Peru"
]

CATEGORY_IMAGE_MAP = {
    "Control Biométrico": "https://picsum.photos/seed/biometric/800/600",
    "Resistencia Digital": "https://picsum.photos/seed/resistance/800/600",
    "Soberanía Criptográfica": "https://picsum.photos/seed/crypto/800/600",
    "Vigilancia del Leviatán": "https://picsum.photos/seed/surveillance/800/600",
    "Tecnología Descentralizada": "https://picsum.photos/seed/decentralized/800/600",
    "Geopolítica y Macro-Leviatán": "https://picsum.photos/seed/geopolitics/800/600",
    "Medicina y Bioética": "https://picsum.photos/seed/medicine/800/600",
    "Cultura y Psicometría": "https://picsum.photos/seed/culture/800/600",
    "Cine e Ingeniería Social": "https://picsum.photos/seed/cinema/800/600",
    "Deporte y Control Biométrico": "https://picsum.photos/seed/sports/800/600",
    "Ciencia y Sustrato": "https://picsum.photos/seed/science/800/600",
    "Religión y Creencias Masivas": "https://picsum.photos/seed/religion/800/600",
    "Crimen de Estado y Abuso Policial": "https://picsum.photos/seed/policeabuse/800/600",
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

def repair_truncated_json(text: str) -> str:
    """
    Intenta reparar un JSON truncado (típico de LM Studio con contexto corto).
    Estrategia: extraer campos ya cerrados y construir un objeto parcial válido.
    """
    # Extraer todos los campos que ya cerraron correctamente con regex
    repaired = {}
    
    # Buscar campos de string
    for field in ["category", "title", "excerpt"]:
        m = re.search(rf'"{field}"\s*:\s*"((?:[^"\\]|\\.)*)"', text, re.DOTALL)
        if m:
            repaired[field] = m.group(1).replace('\\n', '\n').replace('\\"', '"')
    
    # Buscar fullText — puede estar truncado, tomamos lo que hay
    ft_match = re.search(r'"fullText"\s*:\s*"(.*?)(?:"|$)', text, re.DOTALL)
    if ft_match:
        ft = ft_match.group(1)
        # Limpiar escapes parciales al final
        ft = ft.rstrip('\\').replace('\\n', '\n').replace('\\"', '"')
        if not ft.endswith('.'):
            ft += ' [Transmisión cortada — fragmento recuperado por el sistema Ágora.]'
        repaired["fullText"] = ft
    
    # featured
    feat_m = re.search(r'"featured"\s*:\s*(true|false)', text)
    repaired["featured"] = feat_m.group(1) == 'true' if feat_m else False
    
    if "title" in repaired and "fullText" in repaired:
        logging.info("[*] JSON reparado por extracción de campos parciales.")
        return json.dumps(repaired, ensure_ascii=False)
    
    return ""

def slugify(text: str) -> str:
    """Genera un slug de URL a partir de un título."""
    text = text.lower()
    text = re.sub(r'[^a-z0-9\s-]', '', text)
    text = re.sub(r'[\s-]+', '-', text)
    return text.strip('-')

def get_real_world_topic() -> str:
    """Extrae la noticia más relevante del mundo/Perú vía RSS para usarla como semilla."""
    rss_urls = [
        "https://news.google.com/rss/search?q=peru+geopolitica+OR+tecnologia+OR+control&hl=es-419&gl=PE&ceid=PE:es-419",
        "https://news.google.com/rss/search?q=inteligencia+artificial+OR+biometria+OR+vigilancia&hl=es-419&gl=PE&ceid=PE:es-419"
    ]
    try:
        url = random.choice(rss_urls)
        logging.info(f"[*] Escaneando matriz RSS global...")
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            items = root.findall('.//item')
            if items:
                # Elegir uno de los top 5 resultados aleatoriamente
                top_items = items[:5]
                chosen = random.choice(top_items)
                title = chosen.find('title').text
                logging.info(f"[*] Anomalía RSS detectada: {title}")
                return title
    except Exception as e:
        logging.warning(f"[!] Fallo al escanear RSS: {e}. Usando semilla interna.")
    return random.choice(DEFAULT_QUERIES)

def run_investigation(topic: str = None) -> Tuple[bool, str]:
    """Realiza la búsqueda de noticias reales en DuckDuckGo."""
    query = topic if topic else get_real_world_topic()
    logging.info(f"[*] Iniciando inmersión en DDG sobre: '{query}'...")
    
    search_tool = WebSearch()
    res = search_tool.execute(query=query)
    
    if not res.success:
        logging.error(f"[!] Error en búsqueda web: {res.stderr}")
        return False, f"Error en búsqueda web: {res.stderr}"
    
    return True, res.stdout

def write_article(search_results: str, prompt_override: str = None) -> Dict[str, Any]:
    """Usa el LLM de Gravity para redactar la noticia basada en los libros de lore y el contexto web."""
    print("[*] Iniciando motor cognitivo para redacción del artículo...")
    
    # 1. Intentar obtener el proveedor configurado por defecto o bloqueado
    provider_manager.scan_all()
    best_p, best_m = provider_manager.get_best()
    
    # Cargar el Manifiesto Base para alinear ideológicamente a la IA
    manifesto_path = os.path.join(BASE_DIR, "agora_manifesto.txt")
    manifesto_text = ""
    if os.path.exists(manifesto_path):
        with open(manifesto_path, "r", encoding="utf-8") as f:
            manifesto_text = f.read()

    system_prompt = (
        f"{manifesto_text}\n\n"
        "Eres Gravity, un analista, periodista internacional e investigador científico-filosófico de altísimo nivel. "
        "Tu misión es realizar periodismo de investigación profundo a nivel internacional, pero con un ÉNFASIS ESPECIAL EN PERÚ. "
        "Debes analizar los eventos reales (obtenidos de tu búsqueda web) a través del marco analítico "
        "de nuestros libros: 'La Voluntad Soberana', 'La Física del Poder', 'Convergencia Entrópica', 'El Cero Operativo' y 'El Sustrato Primordial'.\n\n"
        "Reglas estrictas de redacción:\n"
        "1. Realiza un análisis riguroso aplicando el 'Ojo de IA' (Reconocimiento de Patrones Avanzado): encuentra correlaciones ocultas, agendas subliminales y ecosistemas invisibles que un humano normal pasaría por alto (ej. relaciona eventos deportivos con extracción biométrica, o estrenos de cine con condicionamiento psicológico masivo).\n"
        "2. Nombra y cita explícitamente a los MEDIOS DE COMUNICACIÓN VERIFICADOS que encuentres en los resultados de búsqueda para dar máxima credibilidad.\n"
        "3. Redacta en ESPAÑOL con óptica materialista y profunda. Asocia la coyuntura (ya sea política, científica, médica, deportiva o cultural) con la extracción de 'trabajo cognitivo', la 'homeostasis' del poder y el 'colapso probabilístico'.\n\n"
        "REGLAS CRÍTICAS DE FORMATO JSON (ANTI-CRASH):\n"
        "- Devuelve ÚNICAMENTE un objeto JSON bien estructurado.\n"
        "- DEBES escapar todos los saltos de línea en el texto escribiendo literalmente \\n.\n"
        "- NUNCA uses saltos de línea literales (raw newlines) dentro de los valores de las cadenas.\n"
        "- DEBES escapar cualquier comilla doble interna usando \\\".\n\n"
        "El formato exacto es:\n"
        "{\n"
        "  \"category\": \"Una de estas: 'Control Biométrico', 'Resistencia Digital', 'Soberanía Criptográfica', 'Vigilancia del Leviatán', 'Tecnología Descentralizada', 'Geopolítica y Macro-Leviatán', 'Medicina y Bioética', 'Cultura y Psicometría', 'Cine e Ingeniería Social', 'Deporte y Control Biométrico', 'Ciencia y Sustrato', 'Religión y Creencias Masivas', 'Crimen de Estado y Abuso Policial'\",\n"
        "  \"title\": \"Título impactante, geopolítico y revelador del reporte\",\n"
        "  \"excerpt\": \"Un resumen analítico y persuasivo de 2-3 líneas exponiendo el patrón oculto descubierto\",\n"
        "  \"fullText\": \"Contenido detallado en Markdown. Usa subsecciones ###. Cita las fuentes de medios de noticias. Recuerda usar \\n para los saltos de línea.\",\n"
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
    
    # Detectar si el proveedor principal está muerto (401) para saltar directo al alternativo
    principal_dead = False
    if best_p:
        try:
            probe_opts = {"temperature": 0.1, "max_tokens": 10}
            probe_msgs = [{"role": "user", "content": "ping"}]
            provider_manager.complete(messages=probe_msgs, model=best_m, provider=best_p.name, options=probe_opts)
        except Exception as probe_err:
            if "401" in str(probe_err) or "Unauthorized" in str(probe_err):
                logging.warning(f"[!] Proveedor principal {best_p.name} rechaza con 401. Saltando directamente a alternativo.")
                principal_dead = True

    # LM Studio tiene límite de contexto menor — reducir tokens para evitar truncamiento
    def get_opts_for_provider(provider_name: str) -> dict:
        if provider_name and "lm studio" in provider_name.lower():
            return {"temperature": 0.5, "max_tokens": 2000}
        return {"temperature": 0.5, "max_tokens": 3500}

    max_retries = 3
    for attempt in range(1, max_retries + 1):
        logging.info(f"[*] Intento de generación {attempt}/{max_retries}...")
        response_raw = ""
        try:
            if best_p and not principal_dead:
                logging.info(f"[*] Intentando con proveedor principal: {best_p.name} | Modelo: {best_m}")
                response_raw = provider_manager.complete(messages=messages, model=best_m, provider=best_p.name, options=get_opts_for_provider(best_p.name))
            else:
                logging.warning("[!] No se encontró un proveedor configurado o está muerto, escalando a alternativo.")
        except Exception as e:
            if "401" in str(e) or "Unauthorized" in str(e):
                logging.warning(f"[!] Proveedor principal devuelve 401. Marcando como muerto para este ciclo.")
                principal_dead = True
            else:
                logging.warning(f"[!] Fallo con el proveedor principal: {e}")
            
        if not response_raw or ("\"title\"" not in response_raw.lower() or "\"fulltext\"" not in response_raw.lower()):
            logging.info("[*] Buscando proveedores alternativos en línea...")
            scans = provider_manager.scan_all(force=True)
            healthy_providers = [s for s in scans if s.is_healthy and s.models and s.name != (best_p.name if best_p else "")]
            if healthy_providers:
                alt_p = healthy_providers[0]
                alt_m = alt_p.active_model or alt_p.models[0]["name"]
                logging.info(f"[+] Proveedor alternativo: {alt_p.name} | Modelo: {alt_m}")
                try:
                    response_raw = provider_manager.complete(messages=messages, model=alt_m, provider=alt_p.name, options=get_opts_for_provider(alt_p.name))
                except Exception as e2:
                    logging.warning(f"[!] Fallo con alternativo: {e2}")

        if not response_raw:
            logging.error(f"[!] Ningún motor generó texto en el intento {attempt}.")
        else:
            clean_resp = clean_llm_response(response_raw)
            try:
                article_data = json.loads(clean_resp, strict=False)
                logging.info("[green]✓ Redacción completada y parseada exitosamente.[/]")
                # Salir del loop si tuvo éxito
                break
            except Exception as e:
                logging.warning(f"[!] Error parseando JSON en intento {attempt}: {e}. Intentando regex...")
                json_match = re.search(r'(\{[\s\S]*\})', clean_resp)
                if json_match:
                    try:
                        article_data = json.loads(json_match.group(1), strict=False)
                        logging.info("[green]✓ JSON extraído por regex.[/]")
                        break
                    except Exception:
                        pass
                # Último recurso: reparador de JSON truncado
                repaired_str = repair_truncated_json(clean_resp)
                if repaired_str:
                    try:
                        article_data = json.loads(repaired_str, strict=False)
                        logging.info("[green]✓ JSON reparado por extracción de campos parciales.[/]")
                        break
                    except Exception:
                        pass
        
        # Si llega aquí, falló el parseo o no hubo respuesta
        if attempt == max_retries:
            logging.error("[!] Fallo crónico de redacción tras múltiples intentos.")
            raise RuntimeError("El modelo no devolvió un JSON estructurado válido tras 3 intentos.")
            
        logging.info("[*] Respirando 10 segundos antes del siguiente intento...")
        time.sleep(10)
        
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
    normalized["date"] = datetime.now().isoformat()
    base_img = CATEGORY_IMAGE_MAP.get(category, CATEGORY_IMAGE_MAP["default"])
    # Añadimos los primeros 15 caracteres del slug al seed de la imagen para que sea única por artículo
    normalized["image"] = base_img.replace("/800/600", f"-{normalized['id'][:15]}/800/600")
    
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
    logging.info(f"[+] Artículo '{new_article.get('title', 'Sin Título')}' agregado con éxito a news.json")

def generate_sitemap():
    """Genera un archivo sitemap.xml básico en la carpeta public de Vite para SEO."""
    public_dir = os.path.join(PORTAL_DIR, "public")
    sitemap_path = os.path.join(public_dir, "sitemap.xml")
    
    if not os.path.exists(public_dir):
        os.makedirs(public_dir, exist_ok=True)
        
    try:
        with open(NEWS_JSON_PATH, "r", encoding="utf-8") as f:
            news_list = json.load(f)
    except Exception:
        news_list = []

    base_url = "https://nexo-agora.netlify.app"
    
    xml_content = '<?xml version="1.0" encoding="UTF-8"?>\n'
    xml_content += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    
    # Homepage
    xml_content += f'  <url>\n    <loc>{base_url}/</loc>\n    <changefreq>daily</changefreq>\n    <priority>1.0</priority>\n  </url>\n'
    
    # News articles
    for article in news_list:
        article_id = article.get("id", "")
        if article_id:
            xml_content += f'  <url>\n    <loc>{base_url}/?article={urllib.parse.quote(article_id)}</loc>\n    <changefreq>weekly</changefreq>\n    <priority>0.8</priority>\n  </url>\n'
            
    xml_content += '</urlset>'
    
    with open(sitemap_path, "w", encoding="utf-8") as f:
        f.write(xml_content)
    logging.info("[green]✓ Sitemap.xml generado y actualizado con éxito.[/]")

def publish_changes():
    """Ejecuta sincronización de libros locales y publica en Netlify mediante git push."""
    logging.info("[*] Sincronizando biblioteca física local...")
    sync_script = os.path.join(PORTAL_DIR, "sync_books.js")
    
    try:
        # Sincronizar libros primero
        subprocess.run(["node", sync_script], cwd=PORTAL_DIR, check=True)
        logging.info("[green]✓ Biblioteca sincronizada con éxito.[/]")
    except Exception as e:
        logging.error(f"[!] Error ejecutando sync_books.js: {e}")
        
    logging.info("[*] Actualizando Sitemap SEO...")
    generate_sitemap()
        
    logging.info("[*] Preparando publicación en GitHub para despliegue automático en Netlify...")
    try:
        # Forzar configuración global de seguridad en Git para el usuario actual (ej. Administrador)
        subprocess.run(["git", "config", "--global", "--add", "safe.directory", "*"], check=False)
        
        # Git Status check
        subprocess.run(["git", "status"], cwd=PORTAL_DIR, check=True)
        
        # Git Add
        subprocess.run(["git", "add", "."], cwd=PORTAL_DIR, check=True)
        
        # Git Commit
        commit_msg = f"Gravity Reporter: reporte de investigación autónomo [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]"
        subprocess.run(["git", "commit", "-m", commit_msg], cwd=PORTAL_DIR, check=True)
        
        # Git Push
        subprocess.run(["git", "push", "origin", "main"], cwd=PORTAL_DIR, check=True)
        logging.info("[green]✓ Publicación exitosa. Netlify se actualizará en segundos.[/]")
    except subprocess.CalledProcessError as e:
        logging.error(f"[!] Error ejecutando comandos de Git: {e}. Asegúrate de que las credenciales estén configuradas en Git global.")
    except Exception as e:
        logging.error(f"[!] Error inesperado al publicar: {e}")

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Gravity AI - Reportero Autónomo")
    parser.add_argument("--topic", type=str, default=None, help="Tema de investigación específico")
    parser.add_argument("--focus", type=str, default=None, help="Enfoque particular de redacción")
    args = parser.parse_args()
    
    logging.info("======================================================================")
    logging.info(f"  Gravity AI Reporter V16.0 PRO - Ejecución: {datetime.now().isoformat()}")
    logging.info("======================================================================")
    
    # 1. Investigar
    success, search_results = run_investigation(args.topic)
    if not success:
        logging.error(f"[!] {search_results}")
        sys.exit(1)
        
    # 2. Redactar
    try:
        article = write_article(search_results, args.focus)
    except Exception as e:
        logging.error(f"[!] Error de redacción por IA: {e}")
        sys.exit(1)
        
    # 3. Guardar en portal
    update_news_json(article)
    
    # 4. Sincronizar y publicar en Netlify
    publish_changes()
    
    logging.info("[*] Proceso completado exitosamente.")

if __name__ == "__main__":
    main()
