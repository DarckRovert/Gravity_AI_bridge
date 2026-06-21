import yt_dlp
import os
import json
import tempfile
import sys

# Asegurar path
current_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(current_dir)
if base_dir not in sys.path:
    sys.path.append(base_dir)

from core import provider_manager
from core.logger import log

class YouTubeAnalyzer:
    def __init__(self):
        self.tmp_dir = os.path.join(base_dir, "scratch", "yt_downloads")
        os.makedirs(self.tmp_dir, exist_ok=True)

    def fetch_video_info(self, url: str) -> dict:
        ydl_opts = {
            'quiet': True,
            'skip_download': True,
            'writeautomaticsub': True,
            'subtitleslangs': ['es', 'en'],
            'outtmpl': os.path.join(self.tmp_dir, '%(id)s.%(ext)s'),
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            
            # Intentar extraer subtítulos directamente de los metadatos si es posible
            transcript = ""
            subs = info.get('requested_subtitles')
            if subs and ('es' in subs or 'en' in subs):
                sub_lang = 'es' if 'es' in subs else 'en'
                # En este nivel yt-dlp solo da la url del vtt/json3
                sub_url = subs[sub_lang].get('url')
                if sub_url:
                    import requests
                    try:
                        r = requests.get(sub_url)
                        if r.status_code == 200:
                            transcript = self._clean_vtt(r.text)
                    except Exception as e:
                        log.error(f"[YT Analyzer] Error bajando subtítulos: {e}")

            if not transcript:
                log.info("[YT Analyzer] No hay subtítulos automáticos. Pasando a Fallback Whisper.")
                transcript = self._fallback_whisper(url, info.get('id', 'temp'))

            return {
                "title": info.get("title", "Unknown"),
                "channel": info.get("uploader", "Unknown"),
                "views": info.get("view_count", 0),
                "duration": info.get("duration", 0),
                "thumbnail": info.get("thumbnail", ""),
                "transcript": transcript
            }

    def _clean_vtt(self, vtt_text: str) -> str:
        import re
        lines = vtt_text.splitlines()
        clean_lines = []
        for line in lines:
            # Eliminar timestamps de VTT y etiquetas HTML/cues
            if '-->' in line or line.startswith('WEBVTT') or line.startswith('Kind:') or line.startswith('Language:'):
                continue
            line = re.sub(r'<[^>]+>', '', line).strip()
            if line and line not in clean_lines[-5:]: # Evitar duplicados simples
                clean_lines.append(line)
        return " ".join(clean_lines)

    def _fallback_whisper(self, url: str, video_id: str) -> str:
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            log.warning("faster-whisper no está instalado. Instalándolo automáticamente...")
            import subprocess
            subprocess.run([sys.executable, "-m", "pip", "install", "faster-whisper"], check=True)
            from faster_whisper import WhisperModel

        audio_file = os.path.join(self.tmp_dir, f"{video_id}.mp3")
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': os.path.join(self.tmp_dir, f"{video_id}.%(ext)s"),
            'quiet': True,
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
                
            log.info("[YT Analyzer] Audio descargado. Iniciando transcripción con Whisper...")
            model = WhisperModel("tiny", device="cpu", compute_type="int8") # Usamos tiny por velocidad
            segments, _ = model.transcribe(audio_file)
            transcript = " ".join([segment.text for segment in segments])
            
            # Limpiar
            if os.path.exists(audio_file):
                os.remove(audio_file)
                
            return transcript
        except Exception as e:
            log.error(f"[YT Analyzer] Falló transcripción por audio: {e}")
            return f"[No se pudo extraer transcripción de audio: {e}]"

    def analyze_with_ai(self, transcript: str, title: str) -> dict:
        prompt = f"""
Actúa como un experto analizador de contenido y estratega de monetización para YouTube.
Acabo de transcribir el siguiente video titulado "{title}".

TRANSCRIPCIÓN:
{transcript[:15000]} # Limitamos a ~15k caracteres por seguridad de contexto

Por favor analiza el video y devuélveme un JSON estricto y válido con esta estructura. 
CRÍTICO: Escapa correctamente las comillas dobles y usa \\n para saltos de línea si los necesitas. No añadas nada fuera del JSON.
{{
    "summary": "Un resumen conciso pero profundo de 3-4 líneas del video.",
    "key_takeaways": ["Punto clave 1", "Punto clave 2", "Punto clave 3"],
    "monetization_strategy": "Una estrategia brillante y creativa de cómo este video puede ser monetizado, o cómo yo puedo replicar este modelo de negocio/contenido para ganar dinero."
}}
        """
        
        try:
            log.info("[YT Analyzer] Consultando a la IA...")
            messages = [{"role": "user", "content": prompt}]
            response = provider_manager.complete(messages)
            if hasattr(response, "text"):
                result_text = response.text
            else:
                result_text = str(response)
                
            # Limpiar posible markdown
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
                
            try:
                return json.loads(result_text)
            except json.JSONDecodeError as json_e:
                log.error(f"[YT Analyzer] JSON inválido devuelto por la IA: {json_e}")
                # Fallback suave si la IA se equivocó en el formato
                return {
                    "summary": "Análisis completado pero el formato devuelto por la IA fue inválido.",
                    "key_takeaways": ["Revisar logs para el raw text."],
                    "monetization_strategy": result_text[:800] + "..."
                }
        except Exception as e:
            log.error(f"[YT Analyzer] Error de IA: {e}")
            return {
                "summary": "No se pudo generar el análisis por parte de la IA.",
                "key_takeaways": [],
                "monetization_strategy": "Intenta de nuevo."
            }

    def process_url(self, url: str) -> dict:
        log.info(f"[YT Analyzer] Procesando {url}...")
        info = self.fetch_video_info(url)
        
        # Si la transcripción es excesivamente corta (ej música) o falló
        if len(info['transcript'].strip()) < 50:
            analysis = {
                "summary": "El video no contiene suficiente diálogo hablado para generar un resumen.",
                "key_takeaways": [],
                "monetization_strategy": "Análisis de monetización no aplicable (falta de contenido verbal)."
            }
        else:
            analysis = self.analyze_with_ai(info['transcript'], info['title'])
            
        info["analysis"] = analysis
        return info
