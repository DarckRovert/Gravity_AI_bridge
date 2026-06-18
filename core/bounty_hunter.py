"""
Gravity AI — Bounty Hunter / Auto-Agency V1.0
Escanea feeds de trabajo freelance (Freelancer.com), filtra ofertas relevantes y 
genera Cover Letters hiper-optimizadas con el LLM activo.
"""

import threading
import time
import json
import urllib.request
import os
from datetime import datetime

from core.logger import log
from core.provider_manager import get_plugin
from core.config_manager import config

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BOUNTIES_FILE = os.path.join(_BASE_DIR, "BOUNTIES_ENCONTRADOS.md")
POLL_INTERVAL_SEC = 1800  # 30 minutos

import xml.etree.ElementTree as ET

def fetch_freelancer_rss():
    """Descarga el feed RSS global de Freelancer.com."""
    url = "https://www.freelancer.com/rss.xml"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read()
            root = ET.fromstring(data)
            items = []
            for item in root.findall('./channel/item'):
                title = item.find('title')
                desc = item.find('description')
                link = item.find('link')
                guid = item.find('guid') # Usamos el guid como ID único
                
                items.append({
                    "id": guid.text if guid is not None else link.text,
                    "title": title.text if title is not None else "",
                    "selftext": desc.text if desc is not None else "",
                    "url": link.text if link is not None else ""
                })
            return items
    except Exception as e:
        log.error(f"[BountyHunter] Error scraping Freelancer RSS: {e}")
        return []

def fetch_reddit_json():
    """Descarga los últimos posts de r/forhire usando JSON (sin autenticación estricta)."""
    url = "https://www.reddit.com/r/forhire/new.json?limit=15"
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "GravityAIBot/16.0 (by DarckRovert) Desktop/Windows"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            items = []
            for child in data.get("data", {}).get("children", []):
                post = child.get("data", {})
                
                items.append({
                    "id": post.get("name"), # t3_...
                    "title": post.get("title", ""),
                    "selftext": post.get("selftext", ""),
                    "url": post.get("url", ""),
                    "platform": "Reddit (r/forhire)"
                })
            return items
    except urllib.error.HTTPError as e:
        if e.code == 403:
            log.warning(f"[BountyHunter] Reddit bloqueó la conexión (403). Ignorando por ahora.")
        else:
            log.error(f"[BountyHunter] Error HTTP en Reddit: {e}")
        return []
    except Exception as e:
        log.error(f"[BountyHunter] Error scraping Reddit JSON: {e}")
        return []

def is_bounty_relevant(title, text):
    """Filtra posts para quedarse solo con trabajos de programación/datos y excluir a los que buscan empleo."""
    title_str = str(title) if title else ""
    text_str = str(text) if text else ""
    title_lower = title_str.lower()
    
    # Excluir gente ofreciendo sus servicios
    if "[for hire]" in title_lower or "[for_hire]" in title_lower:
        return False
        
    # Solo requerimos keywords si estamos en slavelabour, en forhire si tiene [Hiring] casi siempre es bueno.
    # Pero para ser seguros, filtramos por nicho técnico
    keywords = ["python", "scraping", "scrape", "bot", "script", "data entry", "automation", "api", "web", "react", "html", "developer", "sql", "excel", "app", "website", "scrapping"]
    content = (title_str + " " + text_str).lower()
    
    return any(k in content for k in keywords)

def generate_proposal(title, description):
    """Envía la oferta al LLM local para redactar una propuesta persuasiva."""
    bounty_profile = config.get("bounty_profile", "Eres un desarrollador experto buscando trabajo freelance.")
    
    prompt = f"""
{bounty_profile}

He encontrado esta oferta de trabajo:

Título: {title}
Descripción: {description}

Escribe una propuesta corta (Cover Letter / Mensaje directo) para aplicar a este trabajo basándote en tu perfil.
Debe ser muy técnica, profesional, y directa al grano. Convence al cliente de que tienes la infraestructura (IA, Scraping, Automatización) para resolverlo más rápido y mejor que nadie.
Mantenlo conciso (máximo 150 palabras). No pongas un precio exacto a menos que el cliente lo haya pedido explícitamente en la descripción.
No saludes con "Estimado/a", usa algo directo e informal (ej: "Hi there,", "Hey,").

CRITICAL INSTRUCTION: You MUST write the final proposal ENTIRELY in English, regardless of the language of the job description or my profile. Do not write anything in Spanish.
"""
    messages = [{"role": "user", "content": prompt}]
    
    provider_name = config.get("model.default_provider", "LM Studio")
    plugin = get_plugin(provider_name)
    
    if not plugin:
        return f"Error: No se encontró el plugin del proveedor '{provider_name}'."
        
    health = plugin.check_health()
    if not health.is_healthy:
        return f"Error: El proveedor '{provider_name}' no está respondiendo."
        
    try:
        model = health.active_model if health.models else "auto"
        # Usamos chat_stream para obtener la respuesta progresivamente
        chunks = list(plugin.chat_stream(messages, model, {}))
        return "".join(chunks)
    except Exception as e:
        return f"Error generando la propuesta a través de {provider_name}: {e}"

def _init_bounties_file():
    """Crea el archivo con un encabezado si no existe."""
    if not os.path.exists(BOUNTIES_FILE):
        with open(BOUNTIES_FILE, "w", encoding="utf-8") as f:
            f.write("# 💰 GRAVITY AI: Bounty Hunter - Trabajos Freelance Encontrados\n")
            f.write("Aquí irán apareciendo los trabajos técnicos extraídos de Freelancer.com con su propuesta de venta lista para que copies, pegues y cobres.\n\n")
            f.write("---\n\n")

SEEN_IDS_FILE = os.path.join(_BASE_DIR, "inputs", ".bounty_seen_ids.json")

def load_seen_ids():
    if os.path.exists(SEEN_IDS_FILE):
        try:
            with open(SEEN_IDS_FILE, "r", encoding="utf-8") as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()

def save_seen_ids(seen_ids):
    # Ensure inputs directory exists
    os.makedirs(os.path.dirname(SEEN_IDS_FILE), exist_ok=True)
    try:
        with open(SEEN_IDS_FILE, "w", encoding="utf-8") as f:
            json.dump(list(seen_ids)[-500:], f) # Keep only the last 500 to prevent infinite growth
    except Exception as e:
        log.error(f"[BountyHunter] Error guardando cache de IDs: {e}")

def limit_bounties_file():
    """Mantiene solo los últimos 150 contratos en el archivo para evitar colapsos."""
    if not os.path.exists(BOUNTIES_FILE):
        return
    try:
        with open(BOUNTIES_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        import re
        blocks = re.split(r'(?=\n## 🎯 Oportunidad:)', "\n" + content)
        if len(blocks) > 150:
            header = "# 💰 GRAVITY AI: Bounty Hunter - Trabajos Freelance Encontrados\nAquí irán apareciendo los trabajos técnicos extraídos con su propuesta de venta lista para que copies, pegues y cobres.\n\n---\n\n"
            kept_blocks = blocks[-150:]
            with open(BOUNTIES_FILE, "w", encoding="utf-8") as f:
                f.write(header + "".join(kept_blocks).strip() + "\n\n")
    except Exception as e:
        log.error(f"[BountyHunter] Error limitando el archivo: {e}")

def bounty_loop():
    log.info(f"[BountyHunter] Demonio activado. Monitoreando micro-trabajos cada {POLL_INTERVAL_SEC//60} min.")
    _init_bounties_file()
    
    seen_ids = load_seen_ids()
    
    while True:
        try:
            new_bounties = 0
            posts = fetch_freelancer_rss() + fetch_reddit_json()
            for post in posts:
                p_id = post.get("id")
                
                if not p_id or p_id in seen_ids:
                    continue
                    
                title = post.get("title", "")
                text = post.get("selftext", "")
                url = post.get("url", "")
                platform = post.get("platform", "Freelancer.com")
                
                if is_bounty_relevant(title, text):
                    log.info(f"[BountyHunter] 🎯 Nuevo micro-trabajo detectado: {title}")
                    proposal = generate_proposal(title, text)
                    
                    import re
                    # Limpiar chain-of-thought (modelos como DeepSeek-R1)
                    proposal = re.sub(r'<think>.*?</think>', '', proposal, flags=re.DOTALL).strip()
                    
                    if proposal.startswith("Error"):
                        log.warning(f"[BountyHunter] Ignorando trabajo debido a fallo del LLM: {proposal}")
                        # Lo marcamos como visto para no reintentar infinitamente
                        seen_ids.add(p_id)
                        continue
                        
                    with open(BOUNTIES_FILE, "a", encoding="utf-8") as f:
                        f.write(f"## 🎯 Oportunidad: {title}\n")
                        f.write(f"**Plataforma:** {platform} | **Detectado:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                        f.write(f"**Enlace original:** {url}\n\n")
                        f.write(f"### Descripción Original del Cliente\n")
                        desc_trunc = text[:800] + "..." if len(text) > 800 else text
                        # Freelancer a veces devuelve tags HTML en descripcion
                        import re
                        desc_trunc = re.sub(r'<[^>]+>', '', desc_trunc)
                        f.write(f"```text\n{desc_trunc}\n```\n\n")
                        f.write(f"### Propuesta de Venta Generada por IA (Copiar y Enviar)\n")
                        f.write(f"> {proposal.replace(chr(10), chr(10)+'> ')}\n\n")
                        f.write("---\n\n")
                        
                    seen_ids.add(p_id)
                    new_bounties += 1
                    
                    # Auto-Pilot 100%: Enviar al Infiltrador directamente si es de Freelancer
                    if platform == "Freelancer.com":
                        try:
                            from core import infiltrator
                            infiltrator.manager.queue_task({"type": "freelancer_bid", "url": url, "proposal": proposal})
                            log.info(f"[BountyHunter] 🚀 Oferta inyectada al Infiltrador en Full Auto-Pilot.")
                        except Exception as e:
                            log.error(f"[BountyHunter] Error en Auto-Pilot: {e}")
                else:
                    seen_ids.add(p_id)
                    
            if new_bounties > 0:
                log.info(f"[BountyHunter] Se han añadido {new_bounties} nuevas propuestas listas a {BOUNTIES_FILE}.")
                save_seen_ids(seen_ids)
                limit_bounties_file()
            else:
                save_seen_ids(seen_ids)
                
        except Exception as e:
            log.error(f"[BountyHunter] Error en el loop de monitoreo: {e}")
            
        time.sleep(POLL_INTERVAL_SEC)

def start():
    """Punto de entrada usado por core.service_loader"""
    t = threading.Thread(target=bounty_loop, daemon=True, name="BountyHunterWorker")
    t.start()
    return True

if __name__ == "__main__":
    start()
    while True:
        time.sleep(1)
