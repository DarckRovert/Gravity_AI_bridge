import yt_dlp
import os
import json
import sys

# Asegurar path
current_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(current_dir)
if base_dir not in sys.path:
    sys.path.append(base_dir)

from core import provider_manager  # noqa: E402
from core.logger import log  # noqa: E402


class YouTubeAnalyzer:
    def __init__(self):
        self.tmp_dir = os.path.join(base_dir, "scratch", "yt_downloads")
        os.makedirs(self.tmp_dir, exist_ok=True)

    def fetch_video_info(self, url: str) -> dict:
        ydl_opts = {
            "quiet": True,
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": ["es", "en"],
            "outtmpl": os.path.join(self.tmp_dir, "%(id)s.%(ext)s"),
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(url, download=False)
            except Exception as e:
                raise ValueError(
                    f"No se pudo extraer información del video de YouTube: {e}"
                )

            if not info:
                raise ValueError("No se pudieron obtener los metadatos del video.")

            # Extraer subtítulos directamente de los metadatos (manuales o automáticos)
            transcript = ""
            all_subs = info.get("subtitles") or {}
            all_auto = info.get("automatic_captions") or {}

            # Prioridad de idiomas: español ('es*') > inglés ('en*') > otros disponibles
            target_langs = []
            for pool in (all_subs, all_auto):
                for lang in pool.keys():
                    if lang.startswith("es") and lang not in target_langs:
                        target_langs.append(lang)
                for lang in pool.keys():
                    if lang.startswith("en") and lang not in target_langs:
                        target_langs.append(lang)

            for pool in (all_subs, all_auto):
                if transcript:
                    break
                for lang in target_langs:
                    formats = pool.get(lang, [])
                    if not isinstance(formats, list):
                        continue
                    vtt_fmt = next((f for f in formats if f.get("ext") == "vtt"), None)
                    chosen_fmt = vtt_fmt or (formats[0] if formats else None)
                    sub_url = chosen_fmt.get("url") if chosen_fmt else None
                    if sub_url:
                        import requests

                        try:
                            r = requests.get(
                                sub_url,
                                headers={"User-Agent": "Mozilla/5.0"},
                                timeout=15,
                            )
                            if r.status_code == 200 and r.text.strip():
                                transcript = self._clean_vtt(r.text)
                                if transcript:
                                    log.info(
                                        f"[YT Analyzer] Subtítulos extraídos exitosamente ({lang}, {len(transcript)} chars)."
                                    )
                                    break
                        except Exception as e:
                            log.warning(
                                f"[YT Analyzer] Error descargando subtítulos para idioma {lang}: {e}"
                            )

            if not transcript:
                log.info(
                    "[YT Analyzer] No hay subtítulos disponibles en metadatos. Pasando a Fallback Whisper."
                )
                transcript = self._fallback_whisper(url, info.get("id", "temp"))

            likes = info.get("like_count") or 0
            comments = info.get("comment_count") or 0
            views = info.get("view_count") or 0

            # Cálculo de engagement
            engagement_rate = 0
            if views and views > 0:
                engagement_rate = round(((likes + comments) / views) * 100, 2)

            return {
                "title": info.get("title", "Unknown"),
                "channel": info.get("uploader", "Unknown"),
                "views": views,
                "likes": likes,
                "comments": comments,
                "engagement_rate": engagement_rate,
                "upload_date": info.get("upload_date", ""),
                "duration": info.get("duration", 0),
                "thumbnail": info.get("thumbnail", ""),
                "transcript": transcript,
            }

    def _clean_vtt(self, vtt_text: str) -> str:
        import re

        lines = vtt_text.splitlines()
        clean_lines = []
        for line in lines:
            # Eliminar timestamps de VTT y etiquetas HTML/cues
            if (
                "-->" in line
                or line.startswith("WEBVTT")
                or line.startswith("Kind:")
                or line.startswith("Language:")
            ):
                continue
            line = re.sub(r"<[^>]+>", "", line).strip()
            if line and line not in clean_lines[-5:]:  # Evitar duplicados simples
                clean_lines.append(line)
        return " ".join(clean_lines)

    def _fallback_whisper(self, url: str, video_id: str) -> str:
        try:
            from faster_whisper import WhisperModel
        except ImportError:
            log.warning("[YT Analyzer] faster-whisper no está instalado en este entorno.")
            return "[Transcripción no disponible: no hay subtítulos y faster-whisper no está instalado]"

        audio_file = os.path.join(self.tmp_dir, f"{video_id}.mp3")
        ydl_opts = {
            "format": "bestaudio/best",
            "postprocessors": [
                {
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }
            ],
            "outtmpl": os.path.join(self.tmp_dir, f"{video_id}.%(ext)s"),
            "quiet": True,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])

            log.info(
                "[YT Analyzer] Audio descargado. Iniciando transcripción con Whisper..."
            )
            model = WhisperModel(
                "tiny", device="cpu", compute_type="int8"
            )  # Usamos tiny por velocidad
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
    "monetization_strategy": ["Paso estratégico 1", "Paso estratégico 2", "Paso estratégico 3"],
    "hook_score": 8,
    "tone": "Polémico / Educativo",
    "timestamps": [
        {{"time": "[00:00]", "description": "Introducción y gancho"}},
        {{"time": "[05:30]", "description": "Desarrollo del tema principal"}}
    ]
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
                    "monetization_strategy": ["Error al parsear el JSON."],
                    "hook_score": 0,
                    "tone": "Desconocido",
                    "timestamps": [],
                }
        except Exception as e:
            log.error(f"[YT Analyzer] Error de IA: {e}")
            return {
                "summary": "No se pudo generar el análisis por parte de la IA.",
                "key_takeaways": [],
                "monetization_strategy": [],
                "hook_score": 0,
                "tone": "Error",
                "timestamps": [],
            }

    def process_url(self, url: str) -> dict:
        log.info(f"[YT Analyzer] Procesando {url}...")
        info = self.fetch_video_info(url)

        # Si la transcripción es excesivamente corta (ej música) o falló
        if len(info["transcript"].strip()) < 50:
            analysis = {
                "summary": "El video no contiene suficiente diálogo hablado para generar un resumen.",
                "key_takeaways": [],
                "monetization_strategy": [
                    "Análisis de monetización no aplicable (falta de contenido verbal)."
                ],
                "hook_score": 0,
                "tone": "N/A",
                "timestamps": [],
            }
        else:
            analysis = self.analyze_with_ai(info["transcript"], info["title"])

        info["analysis"] = analysis
        return info
