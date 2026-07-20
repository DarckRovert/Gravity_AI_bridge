import os
import json
import time
import subprocess
import concurrent.futures
import urllib.request
import urllib.error
from datetime import datetime

# Directorio de salida
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(BASE_DIR, "_investigaciones")

class TikTokOSINTEngine:
    def __init__(self):
        os.makedirs(OUT_DIR, exist_ok=True)
        # Diccionario básico de plataformas para el Identity Crossover (Sherlock mode)
        self.platforms = {
            "Twitter": "https://twitter.com/{}",
            "GitHub": "https://github.com/{}",
            "YouTube": "https://www.youtube.com/@{}",
            "Patreon": "https://www.patreon.com/{}",
            "Vimeo": "https://vimeo.com/{}"
        }

    def _check_url(self, platform_name, url):
        """Intenta hacer un HEAD/GET al perfil para ver si existe (HTTP 200)."""
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'
        })
        try:
            # Algunas webs bloquean HEAD, usamos GET con timeout corto
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    return platform_name, True, url
        except urllib.error.HTTPError as e:
            # 404 es no encontrado. 403 puede ser WAF/Cloudflare (inconclusivo pero existe)
            if e.code == 404:
                return platform_name, False, url
            elif e.code in (401, 403):
                return platform_name, "Inconclusive (WAF/Auth)", url
        except Exception:
            pass
        return platform_name, False, url

    def run_identity_crossover(self, username: str) -> dict:
        """Escanea múltiples plataformas en busca del mismo username."""
        username = username.lstrip("@")
        results = {}
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = []
            for plat, url_template in self.platforms.items():
                url = url_template.format(username)
                futures.append(executor.submit(self._check_url, plat, url))
                
            for future in concurrent.futures.as_completed(futures):
                plat, exists, url = future.result()
                results[plat] = {"exists": exists, "url": url}
                
        return results

    def _extract_social_links(self, description: str) -> dict:
        """Extrae enlaces sociales directamente del texto de la bio usando Regex."""
        import re
        links = {}
        # Buscar URLs completas
        urls = re.findall(r'https?://[^\s/$.?#].[^\s]*', description)
        for url in urls:
            if "linktr.ee" in url:
                links["Linktree"] = url
            elif "carrd.co" in url:
                links["Carrd"] = url
            elif "beacons.ai" in url:
                links["Beacons"] = url
            elif "instagram.com" in url:
                links["Instagram"] = url
            elif "twitter.com" in url or "x.com" in url:
                links["Twitter/X"] = url
            elif "youtube.com" in url:
                links["YouTube"] = url
            elif "patreon.com" in url:
                links["Patreon"] = url

        # Buscar menciones a plataformas en texto (ej. "IG: @username", "Twitter: username")
        ig_match = re.search(r'(?:ig|instagram|insta):\s*@?([a-zA-Z0-9_\.-]+)', description, re.IGNORECASE)
        if ig_match and "Instagram" not in links:
            links["Instagram"] = f"https://instagram.com/{ig_match.group(1)}"
            
        tw_match = re.search(r'(?:tw|twitter|x):\s*@?([a-zA-Z0-9_\.-]+)', description, re.IGNORECASE)
        if tw_match and "Twitter/X" not in links:
            links["Twitter/X"] = f"https://x.com/{tw_match.group(1)}"

        tg_match = re.search(r'(?:tg|telegram):\s*@?([a-zA-Z0-9_\.-]+)', description, re.IGNORECASE)
        if tg_match:
            links["Telegram"] = f"https://t.me/{tg_match.group(1)}"

        return links

    def extract_pattern_of_life(self, username: str) -> dict:
        """Usa yt-dlp para descargar la metadata de los últimos 15 videos del usuario."""
        username = username.lstrip("@")
        target_url = f"https://www.tiktok.com/@{username}"
        
        # Ejecutamos yt-dlp en modo JSON, flat-playlist para no bajar los videos reales
        cmd = [
            "yt-dlp",
            "-J",
            "--flat-playlist",
            "--playlist-end", "15",
            target_url
        ]
        
        try:
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8")
            stdout, stderr = process.communicate(timeout=60)
            
            if process.returncode != 0:
                return {"error": stderr.strip()}
                
            data = json.loads(stdout)
            description = data.get("description", "")
            entries = data.get("entries", [])
            
            videos = []
            total_views = 0
            total_likes = 0
            total_comments = 0
            timestamps = []
            
            for v in entries:
                ts = v.get("timestamp")
                v_data = {
                    "id": v.get("id"),
                    "title": v.get("title", ""),
                    "timestamp": ts,
                    "views": v.get("view_count", 0),
                    "likes": v.get("like_count", 0),
                    "comments": v.get("comment_count", 0),
                    "url": v.get("url", "")
                }
                videos.append(v_data)
                total_views += v_data["views"] or 0
                total_likes += v_data["likes"] or 0
                total_comments += v_data["comments"] or 0
                if ts:
                    timestamps.append(ts)
            
            # 1. Enlaces verificados de la bio
            verified_links = self._extract_social_links(description)
            
            # 2. Análisis temporal
            hourly_distribution = {"Madrugada (00-06h)": 0, "Mañana (06-12h)": 0, "Tarde (12-18h)": 0, "Noche (18-00h)": 0}
            weekday_distribution = {"Lunes-Viernes": 0, "Fin de Semana": 0}
            
            for ts in timestamps:
                dt = datetime.fromtimestamp(ts)
                h = dt.hour
                if 0 <= h < 6:
                    hourly_distribution["Madrugada (00-06h)"] += 1
                elif 6 <= h < 12:
                    hourly_distribution["Mañana (06-12h)"] += 1
                elif 12 <= h < 18:
                    hourly_distribution["Tarde (12-18h)"] += 1
                else:
                    hourly_distribution["Noche (18-00h)"] += 1
                
                if dt.weekday() < 5:
                    weekday_distribution["Lunes-Viernes"] += 1
                else:
                    weekday_distribution["Fin de Semana"] += 1
            
            # Calcular engagement
            engagement_rate = 0.0
            if total_views > 0:
                engagement_rate = round(((total_likes + total_comments) / total_views) * 100, 2)
            
            # 3. Mapeo Cognitivo
            cognitive_profile = "No disponible"
            if len(videos) > 0:
                try:
                    video_titles = "\n".join([f"- {v['title']}" for v in videos[:10]])
                    prompt = f"""
                    Analiza la biografía y los títulos de los últimos vídeos de esta cuenta de TikTok:
                    
                    Biografía: {description}
                    Vídeos recientes:
                    {video_titles}
                    
                    Genera un reporte conciso de 3 puntos:
                    1. Foco Temático (temáticas principales y hashtags implícitos).
                    2. Orientación Cognitiva (ideológica, educativa, comercial, entretenimiento, debate conflictivo).
                    3. Target demográfico / Audiencia objetivo.
                    
                    Responde de manera ejecutiva en español, máximo 8 líneas de texto limpio sin formato markdown pesado.
                    """
                    from core.provider_manager import complete
                    cognitive_profile = complete(
                        messages=[
                            {"role": "system", "content": "Eres un analista de inteligencia OSINT y firmas digitales. Das respuestas directas y de alto valor."},
                            {"role": "user", "content": prompt}
                        ],
                        task="any"
                    )
                except Exception:
                    pass
            
            return {
                "bio": description,
                "verified_social_links": verified_links,
                "total_videos_analyzed": len(videos),
                "total_views": total_views,
                "total_likes": total_likes,
                "total_comments": total_comments,
                "engagement_rate_pct": engagement_rate,
                "hourly_activity": hourly_distribution,
                "weekday_activity": weekday_distribution,
                "cognitive_profile": cognitive_profile.strip() if cognitive_profile else "No disponible",
                "videos": videos
            }
        except Exception as e:
            return {"error": str(e)}

    def generate_dossier(self, username: str, radar_data: dict, crossover_data: dict, pol_data: dict) -> str:
        """Genera un reporte Markdown con toda la inteligencia recopilada."""
        username = username.lstrip("@")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"Dossier_OSINT_{username}_{timestamp}.md"
        filepath = os.path.join(OUT_DIR, filename)
        
        doc = [
            f"# Dossier OSINT Táctico: @{username}",
            f"**Fecha de Generación:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "---",
            "## 1. Identificadores Core y Telemetría de Red",
        ]
        
        if radar_data:
            doc.append(f"- **Room ID:** `{radar_data.get('room_id', 'N/A')}`")
            doc.append(f"- **User ID (UID):** `{radar_data.get('user_id', 'N/A')}`")
            doc.append(f"- **Proveedor CDN:** `{radar_data.get('cdn_provider', 'N/A')}`")
            doc.append(f"- **IP Servidor CDN:** `{radar_data.get('cdn_ip', 'N/A')}`")
            doc.append(f"- **Ubicación del Servidor:** `{radar_data.get('geo_city', 'N/A')}, {radar_data.get('geo_country', 'N/A')}`")
            doc.append(f"- **Resolución del Stream:** `{radar_data.get('resolution', 'N/A')}`")
            doc.append(f"- **FPS (Imágenes por segundo):** `{radar_data.get('fps', 0.0)}`")
            doc.append(f"- **Calidad de Audio/Video Codecs:** `V: {radar_data.get('codec_video', 'N/A')} / A: {radar_data.get('codec_audio', 'N/A')}`")
            doc.append(f"- **Bitrate Detectado:** `{radar_data.get('bitrate_kbps', 0)} Kbps`")
            doc.append(f"- **Últimos Viewers:** `{radar_data.get('viewers', 'N/A')}`")
        else:
            doc.append("No hay datos de radar en vivo disponibles.")
            
        doc.append("\n## 2. Identity Crossover (Búsqueda Cruzada)")
        
        # Enlaces verificados de la bio
        verified_links = pol_data.get("verified_social_links", {})
        if verified_links:
            doc.append("### Enlaces Verificados (Extraídos de su Bio)")
            for platform, url in verified_links.items():
                doc.append(f"- [x] **{platform} (Verificado)**: [Visitar]({url})")
            doc.append("")

        doc.append("### Huella Digital por Coincidencia de Nombre:")
        found_any = False
        for plat, info in crossover_data.items():
            if info["exists"] is True:
                doc.append(f"- [x] **{plat}**: [Posible Coincidencia]({info['url']})")
                found_any = True
            elif isinstance(info["exists"], str):
                doc.append(f"- [?] **{plat}**: Requiere verificación manual ({info['exists']}) - [Link]({info['url']})")
        if not found_any and not verified_links:
            doc.append("> No se encontraron coincidencias directas concluyentes.")
            
        doc.append("\n## 3. Patrón de Vida (Actividad Temporal)")
        
        if pol_data.get("error"):
            doc.append(f"> **Error extrayendo patrón de vida:** {pol_data['error']}")
        else:
            doc.append(f"Análisis de los últimos {pol_data.get('total_videos_analyzed', 0)} videos publicados:")
            doc.append(f"- **Vistas Totales (Muestra):** {pol_data.get('total_views', 0):,}")
            doc.append(f"- **Likes Totales (Muestra):** {pol_data.get('total_likes', 0):,}")
            doc.append(f"- **Tasa de Engagement (Reacción/Vistas):** `{pol_data.get('engagement_rate_pct', 0.0)}%` (Likes + Comentarios / Vistas)\n")
            
            # Distribución horaria
            doc.append("### Histograma de Publicación Temporal")
            doc.append("Distribución de posts por hora local (Pico de actividad):")
            for period, count in pol_data.get("hourly_activity", {}).items():
                bars = "█" * count
                doc.append(f"- **{period}:** `{count}` posts {bars}")
            
            doc.append("\nDistribución de posts por días de la semana:")
            for period, count in pol_data.get("weekday_activity", {}).items():
                bars = "█" * count
                doc.append(f"- **{period}:** `{count}` posts {bars}")
                
            # Mapeo cognitivo
            doc.append("\n### Perfil Cognitivo OSINT (Análisis de Temas e Intereses)")
            doc.append(f"> {pol_data.get('cognitive_profile', 'No disponible')}\n")
            
            doc.append("### Cronología de Publicación Reciente")
            doc.append("| Fecha y Hora | Título | Vistas | Likes |")
            doc.append("|---|---|---|---|")
            for v in pol_data.get("videos", []):
                ts_str = datetime.fromtimestamp(v["timestamp"]).strftime('%Y-%m-%d %H:%M') if v.get("timestamp") else "Desconocida"
                title_clean = v["title"].replace("\n", " ").replace("|", " ")[:60] + "..." if len(v["title"]) > 60 else v["title"].replace("\n", " ").replace("|", " ")
                doc.append(f"| {ts_str} | [{title_clean}]({v['url']}) | {v['views']:,} | {v['likes']:,} |")
                
        doc.append("\n---\n*Reporte generado automáticamente por Gravity AI Bridge (GTLIS Suite).*")
        
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(doc))
            
        # Guardar en la Memoria Estratégica Global de Gravity AI
        try:
            from core.strategic_memory import upsert_pattern
            upsert_pattern(f"tiktok:dossier:{username}", "\n".join(doc))
        except Exception as mem_err:
            print(f"[OSINT] Fallo guardando dossier en Memoria Estratégica: {mem_err}")
            
        return filepath
