"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY AI — GTLIS REST API MIXIN V1.0                                      ║
║  Endpoints HTTP para el TikTok Live Intelligence Suite                       ║
╚══════════════════════════════════════════════════════════════════════════════╝

GET  /v1/tiktok/status              → Estado del radar + canales monitoreados
GET  /v1/tiktok/probe?user=HANDLE   → Análisis inmediato de un canal
GET  /v1/tiktok/report?user=HANDLE  → Informe histórico consolidado
GET  /v1/tiktok/channels            → Lista de canales en watchlist
GET  /v1/tiktok/alerts              → Alertas recientes (todas o por canal)
GET  /v1/tiktok/history?user=HANDLE → Historial de snapshots
GET  /v1/tiktok/bot?user=HANDLE     → Bot score del canal
POST /v1/tiktok/watch               → Añadir canal al monitoreo continuo
POST /v1/tiktok/unwatch             → Remover canal del monitoreo
POST /v1/tiktok/analyze             → Análisis OSINT completo bajo demanda
"""

from __future__ import annotations

import os
import json
import urllib.parse
import time
from typing import Any, Dict, Optional

_ROUTE_DIR = os.path.dirname(os.path.abspath(__file__))
_BASE_DIR = os.path.dirname(os.path.dirname(_ROUTE_DIR))

from core.logger import log

_osint_rate_limit = {}


def _json_response(handler, data: Any, status: int = 200) -> None:
    """Helper para enviar respuesta JSON desde el handler HTTP."""
    body = json.dumps(data, ensure_ascii=False, default=str).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler._send_cors()
    handler.end_headers()
    handler.wfile.write(body)


def _parse_qs(path: str) -> Dict[str, str]:
    """Extrae query parameters del path."""
    if "?" not in path:
        return {}
    qs = path.split("?", 1)[1]
    return {k: v[0] for k, v in urllib.parse.parse_qs(qs).items()}


def _read_json_body(handler) -> Optional[Dict[str, Any]]:
    """Lee y parsea el cuerpo JSON de una request POST."""
    try:
        length = int(handler.headers.get("Content-Length", 0))
        if length == 0:
            return {}
        raw = handler.rfile.read(length)
        return json.loads(raw.decode("utf-8"))
    except Exception:
        return None


# ── Lazy import del radar (evita circular imports y carga diferida) ─────────────
def _get_radar():
    from core.tiktok_radar import get_radar
    return get_radar()


def _get_monitor():
    from tools.tiktok_live_monitor import get_monitor
    return get_monitor()


def _get_alerts(username: Optional[str] = None, limit: int = 50):
    from core.tiktok_radar import _get_recent_alerts
    return _get_recent_alerts(username=username, limit=limit)


def _get_history(username: str, limit: int = 50):
    from core.tiktok_radar import _get_history
    return _get_history(username, limit)


# ── TikTok OSINT Mixin ────────────────────────────────────────────────────────


class TikTokMixin:
    """
    Mixin que agrega los endpoints GTLIS al GravityBridgeHandler.
    Heredar junto con BaseHTTPRequestHandler y los otros mixins.
    """

    # ── GET handlers ──────────────────────────────────────────────────────────

    def _serve_tiktok_status(self):
        """
        GET /v1/tiktok/status
        Retorna el estado del TikTokRadar y todos los canales monitoreados.
        """
        try:
            radar = _get_radar()
            status = radar.get_status()
            _json_response(self, status)
        except Exception as exc:
            _json_response(self, {"error": str(exc), "running": False}, 500)

    def _serve_tiktok_channels(self):
        """
        GET /v1/tiktok/channels
        Lista de canales en watchlist con su último snapshot.
        """
        try:
            radar = _get_radar()
            status = radar.get_status()
            _json_response(self, {
                "channels": status.get("channels", []),
                "total": len(status.get("channels", [])),
            })
        except Exception as exc:
            _json_response(self, {"error": str(exc), "channels": []}, 500)

    def _serve_tiktok_probe(self):
        """
        GET /v1/tiktok/probe?user=HANDLE[&action=probe|profile|recon|full]
        Ejecuta un análisis OSINT inmediato sobre el canal especificado.
        """
        params = _parse_qs(self.path)
        raw_user = params.get("user", "").strip()
        
        import re
        if "tiktok.com/" in raw_user:
            match = re.search(r"@([a-zA-Z0-9_.-]+)", raw_user)
            if match:
                raw_user = match.group(1)
            else:
                raw_user = raw_user.split("?")[0].split("/")[-1]
                
        username = raw_user.lstrip("@")
        action = params.get("action", "probe")

        if not username:
            _json_response(
                self,
                {"error": "Se requiere ?user=HANDLE"},
                400,
            )
            return

        try:
            monitor = _get_monitor()
            result = monitor.execute(action=action, username=username)
            if result.success:
                _json_response(self, result.data)
            else:
                _json_response(self, {"error": result.stderr, "username": username}, 422)
        except Exception as exc:
            _json_response(self, {"error": str(exc)}, 500)

    def _serve_tiktok_report(self):
        """
        GET /v1/tiktok/report?user=HANDLE
        Retorna el informe histórico consolidado de un canal.
        """
        params = _parse_qs(self.path)
        username = params.get("user", "").lstrip("@")

        if not username:
            _json_response(self, {"error": "Se requiere ?user=HANDLE"}, 400)
            return

        try:
            radar = _get_radar()
            report = radar.get_report(username)
            _json_response(self, report)
        except Exception as exc:
            _json_response(self, {"error": str(exc)}, 500)

    def _serve_tiktok_alerts(self):
        """
        GET /v1/tiktok/alerts[?user=HANDLE&limit=N]
        Retorna las alertas recientes, opcionalmente filtradas por canal.
        """
        params = _parse_qs(self.path)
        username = params.get("user", "").lstrip("@") or None
        try:
            limit = int(params.get("limit", "50"))
        except ValueError:
            limit = 50

        try:
            alerts = _get_alerts(username=username, limit=limit)
            _json_response(self, {"alerts": alerts, "total": len(alerts)})
        except Exception as exc:
            _json_response(self, {"error": str(exc), "alerts": []}, 500)

    def _serve_tiktok_history(self):
        """
        GET /v1/tiktok/history?user=HANDLE[&limit=N]
        Retorna el historial de snapshots de un canal.
        """
        params = _parse_qs(self.path)
        username = params.get("user", "").lstrip("@")
        try:
            limit = int(params.get("limit", "50"))
        except ValueError:
            limit = 50

        if not username:
            _json_response(self, {"error": "Se requiere ?user=HANDLE"}, 400)
            return

        try:
            history = _get_history(username, limit)
            _json_response(self, {"username": username, "snapshots": history, "total": len(history)})
        except Exception as exc:
            _json_response(self, {"error": str(exc), "snapshots": []}, 500)

    def _serve_tiktok_bot_analyze(self):
        """
        GET /v1/tiktok/bot?user=HANDLE
        Ejecuta análisis de bot score usando comentarios del chat real si están disponibles.
        """
        params = _parse_qs(self.path)
        username = params.get("user", "").lstrip("@")

        if not username:
            _json_response(self, {"error": "Se requiere ?user=HANDLE"}, 400)
            return

        try:
            comments = []
            try:
                from core.tiktok_radar import get_radar
                comments = get_radar().get_comments(username)
            except Exception:
                pass

            monitor = _get_monitor()
            if comments:
                res_data = monitor.bot_check(comments)
                _json_response(self, {
                    "username": username,
                    "is_live": True,
                    "bot_score": res_data.get("bot_score", 0.0),
                    "risk_level": res_data.get("risk_level", "low"),
                    "details": res_data.get("signals", []),
                    "note": f"bot_score calculado en base a {len(comments)} comentarios de chat en vivo.",
                })
            else:
                snap = monitor.probe(username)
                _json_response(self, {
                    "username": username,
                    "is_live": snap.is_live,
                    "viewers": snap.viewers,
                    "bot_score": snap.bot_score,
                    "risk_level": (
                        "critical" if snap.bot_score >= 0.7
                        else "high" if snap.bot_score >= 0.4
                        else "medium" if snap.bot_score >= 0.2
                        else "low"
                    ),
                    "note": "bot_score calculado desde métricas del canal (sin chat activo).",
                })
        except Exception as exc:
            _json_response(self, {"error": str(exc)}, 500)

    # ── POST handlers ─────────────────────────────────────────────────────────

    def _serve_tiktok_watch(self):
        """
        POST /v1/tiktok/watch
        Body: {"username": "HANDLE", "interval_sec": 60, "notes": ""}
        Agrega un canal a la watchlist y lo inicia de inmediato.
        """
        body = _read_json_body(self)
        if not body:
            _json_response(self, {"error": "Body JSON requerido"}, 400)
            return

        raw_username = str(body.get("username", "")).strip()
        import re
        if "tiktok.com/" in raw_username:
            match = re.search(r"@([a-zA-Z0-9_.-]+)", raw_username)
            if match:
                raw_username = match.group(1)
            else:
                # Intento de fallback
                raw_username = raw_username.split("?")[0].split("/")[-1]

        username = raw_username.lstrip("@").split("?")[0].split("/")[0]
        interval_sec = int(body.get("interval_sec", 60))
        notes = str(body.get("notes", ""))

        if not username:
            _json_response(self, {"error": "Campo 'username' requerido"}, 400)
            return

        if interval_sec < 15:
            _json_response(
                self,
                {"error": "interval_sec mínimo es 15 segundos para no saturar la API"},
                400,
            )
            return

        try:
            radar = _get_radar()
            result = radar.watch(username, interval_sec, notes)
            _json_response(self, result, 201)
        except Exception as exc:
            _json_response(self, {"error": str(exc)}, 500)

    def _serve_tiktok_unwatch(self):
        """
        POST /v1/tiktok/unwatch
        Body: {"username": "HANDLE"}
        Remueve un canal de la watchlist y detiene su watcher.
        """
        body = _read_json_body(self)
        if not body:
            _json_response(self, {"error": "Body JSON requerido"}, 400)
            return

        username = str(body.get("username", "")).lstrip("@")
        if not username:
            _json_response(self, {"error": "Campo 'username' requerido"}, 400)
            return

        try:
            radar = _get_radar()
            result = radar.unwatch(username)
            _json_response(self, result)
        except Exception as exc:
            _json_response(self, {"error": str(exc)}, 500)

    def _serve_tiktok_analyze(self):
        """
        POST /v1/tiktok/analyze
        Body: {
            "username": "HANDLE",
            "action": "full|probe|profile|recon|bot",
            "stream_url": "https://...",  (opcional)
            "comments": [                  (opcional, para bot detection)
                {"user_id": "123", "text": "...", "timestamp_ms": 1234567890}
            ]
        }
        Análisis OSINT completo bajo demanda.
        """
        body = _read_json_body(self)
        if not body:
            _json_response(self, {"error": "Body JSON requerido"}, 400)
            return

        username = str(body.get("username", "")).lstrip("@")
        action = str(body.get("action", "full"))
        stream_url = str(body.get("stream_url", ""))
        comments = body.get("comments", [])

        if not username and not stream_url:
            _json_response(
                self,
                {"error": "Se requiere 'username' o 'stream_url'"},
                400,
            )
            return

        if action not in ("full", "probe", "profile", "recon", "bot"):
            _json_response(
                self,
                {"error": "action debe ser: full|probe|profile|recon|bot"},
                400,
            )
            return
        try:
            monitor = _get_monitor()
            result = monitor.execute(
                action=action,
                username=username,
                stream_url=stream_url,
                comments=comments,
            )
            if result.success:
                _json_response(self, result.data)
            else:
                _json_response(
                    self,
                    {"error": result.stderr, "username": username},
                    422,
                )
        except Exception as exc:
            _json_response(self, {"error": str(exc)}, 500)

    # ── POST dispatcher (patrón modular Gravity) ──────────────────────────────

    def _serve_tiktok_geo(self):
        """
        GET  /v1/tiktok/geo?user=HANDLE[&stream_url=URL]
        POST /v1/tiktok/geo  Body: {"username":"...", "stream_url":"...", "bio":"...",
                                     "live_title":"...", "comments":[], "live_history":[]}
        Genera el informe de inteligencia geográfica máxima (Módulo 5).
        """
        # Soporta tanto GET como POST
        if self.command == "GET":
            params = _parse_qs(self.path)
            username = params.get("user", "").lstrip("@")
            stream_url = params.get("stream_url", "")
            body = {}
        else:
            body = _read_json_body(self) or {}
            username = str(body.get("username", "")).lstrip("@")
            stream_url = str(body.get("stream_url", ""))

        if not username and not stream_url:
            _json_response(self, {"error": "Se requiere ?user=HANDLE o body con 'username'"}, 400)
            return

        try:
            monitor = _get_monitor()
            
            # Auto-completar datos si la petición es GET simple (desde el frontend)
            if not stream_url or not body.get("bio"):
                try:
                    # 1. Intentar obtener metadata en vivo
                    snap = monitor.probe(username)
                    if not stream_url and snap.stream_url:
                        stream_url = snap.stream_url
                    if not body.get("live_title") and snap.title:
                        body["live_title"] = snap.title
                        
                    # 1.5 Si yt-dlp falló (a veces bloquea), rescatar metadata del radar continuo
                    if not stream_url or not body.get("live_title"):
                        try:
                            from core.tiktok_radar import get_radar
                            rstatus = get_radar().get_status()
                            for ch in rstatus.get("channels", []):
                                if ch.get("username", "").lower() == username.lower() and ch.get("is_live"):
                                    if not stream_url: stream_url = ch.get("stream_url", "")
                                    if not body.get("live_title"): body["live_title"] = ch.get("title", "")
                                    break
                        except Exception:
                            pass

                    # 1.6 Fallback offline: si sigue sin stream_url, buscar último stream en vivo en la base de datos
                    if not stream_url:
                        try:
                            from core.tiktok_radar import _get_last_live_snapshot
                            last_live = _get_last_live_snapshot(username)
                            if last_live and last_live.get("stream_url"):
                                stream_url = last_live.get("stream_url")
                                if not body.get("live_title") and last_live.get("title"):
                                    body["live_title"] = last_live.get("title")
                        except Exception:
                            pass
                        
                    # 2. Intentar obtener bio del perfil
                    prof = monitor.profile(username)
                    if not body.get("bio") and prof.bio:
                        body["bio"] = prof.bio
                        
                    # 3. Obtener historial para inferir huso horario
                    if not body.get("live_history"):
                        history = _get_history(username, limit=20)
                        if history:
                            body["live_history"] = history
                            
                    # 4. Obtener comentarios del colector en vivo real en segundo plano
                    if not body.get("comments"):
                        try:
                            from core.tiktok_radar import get_radar
                            body["comments"] = get_radar().get_comments(username)
                        except Exception:
                            pass
                except Exception as inner_e:
                    log.warning(f"[Geo] Error auto-completando data para {username}: {inner_e}")

            result = monitor.geo_intel(
                username=username,
                stream_url=stream_url,
                bio=str(body.get("bio", "")),
                live_title=str(body.get("live_title", "")),
                comments=body.get("comments") or None,
                live_history=body.get("live_history") or None,
            )
            _json_response(self, result)
        except Exception as exc:
            _json_response(self, {"error": str(exc)}, 500)

    def _serve_tiktok_deep_osint(self):
        """
        GET /v1/tiktok/deep_osint?user=HANDLE
        Ejecuta el escaneo de OSINT profundo y genera el dossier con Rate Limiting.
        """
        params = _parse_qs(self.path)
        username = params.get("user", "").lstrip("@")
        if not username:
            _json_response(self, {"error": "Missing ?user=HANDLE"}, 400)
            return

        now = time.time()
        client_ip = self.client_address[0]
        if client_ip in _osint_rate_limit and now - _osint_rate_limit[client_ip] < 60:
            _json_response(self, {"error": "Rate limit exceeded. Wait 60s antes de otro OSINT profundo."}, 429)
            return
        _osint_rate_limit[client_ip] = now


        try:
            radar = _get_radar()
            filepath = radar.run_full_osint(username)
            if os.path.exists(filepath):
                with open(filepath, "r", encoding="utf-8") as f:
                    content = f.read()
                _json_response(self, {"success": True, "filepath": filepath, "content": content})
            else:
                _json_response(self, {"error": "No se pudo generar el reporte"}, 500)
        except Exception as exc:
            _json_response(self, {"error": str(exc)}, 500)

    def _serve_tiktok_dossier(self):
        """
        GET /v1/tiktok/dossier?user=HANDLE
        Retorna el último dossier generado para este usuario.
        """
        params = _parse_qs(self.path)
        username = params.get("user", "").lstrip("@")
        if not username:
            _json_response(self, {"error": "Se requiere ?user=HANDLE"}, 400)
            return
            
        import glob
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        out_dir = os.path.join(base_dir, "_investigaciones")
        pattern = os.path.join(out_dir, f"Dossier_OSINT_{username}_*.md")
        files = glob.glob(pattern)
        
        if not files:
            _json_response(self, {"error": "No hay dossier disponible"}, 404)
            return
            
        latest_file = max(files, key=os.path.getctime)
        try:
            with open(latest_file, "r", encoding="utf-8") as f:
                content = f.read()
            _json_response(self, {"success": True, "filepath": latest_file, "content": content})
        except Exception as exc:
            _json_response(self, {"error": str(exc)}, 500)

    def _serve_tiktok_chat_suggestions(self):
        """
        GET /v1/tiktok/chat_suggestions?user=HANDLE
        Genera 3 sugerencias de respuesta en base a comentarios reales de chat en vivo.
        """
        params = _parse_qs(self.path)
        username = params.get("user", "").lstrip("@")
        if not username:
            _json_response(self, {"error": "Se requiere ?user=HANDLE"}, 400)
            return

        try:
            comments = []
            try:
                from core.tiktok_radar import get_radar
                comments = get_radar().get_comments(username)
            except Exception:
                pass

            if not comments:
                _json_response(self, {
                    "username": username,
                    "suggestions": [],
                    "note": "No hay comentarios de chat en vivo recolectados para este canal actualmente."
                })
                return

            # Formatear últimos 10 comentarios
            recent_comments = comments[-10:]
            formatted_comments = "\n".join([f"- @{c['user_id']}: {c['text']}" for c in recent_comments])

            # LLM prompt
            prompt = (
                f"Aquí tienes los comentarios recientes de una transmisión en vivo en TikTok del canal @{username}:\n\n"
                f"{formatted_comments}\n\n"
                "Genera 3 sugerencias de respuesta en español que el streamer pueda copiar y pegar directamente para interactuar con la audiencia. "
                "Las sugerencias deben ser:\n"
                "1. Una respuesta amigable de agradecimiento o saludo.\n"
                "2. Una respuesta informativa o de respuesta a preguntas frecuentes/comentarios.\n"
                "3. Una pregunta interactiva para enganchar al chat y subir el engagement.\n\n"
                "Devuelve el resultado estrictamente como un objeto JSON con una única propiedad 'suggestions' que contenga una lista de 3 strings, ejemplo:\n"
                "{\n"
                "  \"suggestions\": [\n"
                "    \"Respuesta 1\",\n"
                "    \"Respuesta 2\",\n"
                "    \"Respuesta 3\"\n"
                "  ]\n"
                "}\n"
                "No agregues explicaciones, introducciones ni bloques markdown. Solo devuelve el JSON válido."
            )

            # Invocar al LLM configurado en Gravity
            from core.provider_manager import complete
            
            system_msg = (
                "Eres un asistente de interacción de redes sociales de Gravity AI. "
                "Generas respuestas sugeridas dinámicas, rápidas y atractivas para streamers. "
                "Salida en formato JSON crudo estrictamente sin formato markdown."
            )
            
            response_text = complete(
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": prompt}
                ],
                task="any"
            )

            # Limpiar posibles delimitadores markdown (```json ... ``` o ```)
            cleaned_text = response_text.strip()
            if cleaned_text.startswith("```"):
                lines = cleaned_text.splitlines()
                # Remover primera línea si empieza con ```
                if lines[0].startswith("```"):
                    lines = lines[1:]
                # Remover última línea si termina con ```
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                cleaned_text = "\n".join(lines).strip()

            try:
                suggestions_data = json.loads(cleaned_text)
                suggestions = suggestions_data.get("suggestions", [])
            except Exception as parse_e:
                # Fallback rústico si el LLM no obedeció el formato JSON
                log.warning(f"[ChatSuggestions] Fallback de parseo de sugerencias: {parse_e}. Texto crudo: {response_text}")
                # Dividir por líneas o números si viene estructurado
                lines = [l.strip().lstrip("1234567890.-* ") for l in response_text.splitlines() if l.strip()]
                suggestions = [l for l in lines if l][:3]

            _json_response(self, {
                "username": username,
                "suggestions": suggestions,
                "note": f"Sugerencias generadas en base a {len(recent_comments)} comentarios de chat."
            })

        except Exception as exc:
            log.error(f"[ChatSuggestions] Error generando sugerencias para {username}: {exc}")
            _json_response(self, {"error": str(exc)}, 500)

    def _serve_tiktok_comments(self):
        """
        GET /v1/tiktok/comments?user=HANDLE
        Retorna la lista de comentarios capturados en memoria junto con métricas rápidas (Léxico + Sentimiento).
        """
        params = _parse_qs(self.path)
        username = params.get("user", "").lstrip("@")
        if not username:
            _json_response(self, {"error": "Se requiere ?user=HANDLE"}, 400)
            return

        try:
            comments = []
            try:
                from core.tiktok_radar import get_radar
                comments = get_radar().get_comments(username)
            except Exception as e:
                log.warning(f"[CommentsAPI] Error obteniendo comentarios para @{username}: {e}")

            # Análisis rápido en tiempo real
            words = {}
            toxic_keywords = ["pendejo", "estupido", "mierda", "basura", "puto", "idiota", "spam", "bot", "tonto", "culero", "cabron"]
            toxic_count = 0
            for c in comments:
                text = c.get("text", "").lower()
                # Contar toxicidad simple
                if any(t in text for t in toxic_keywords):
                    toxic_count += 1
                # Contar palabras (filtrando palabras cortas/artículos comunes)
                for w in text.split():
                    w_clean = "".join(ch for ch in w if ch.isalnum())
                    if len(w_clean) > 3 and w_clean not in ("para", "como", "este", "esta", "todo", "pero", "esta", "bien", "hola"):
                        words[w_clean] = words.get(w_clean, 0) + 1

            sorted_words = sorted(words.items(), key=lambda x: x[1], reverse=True)[:5]
            top_keywords = [w[0] for w in sorted_words]
            toxicity_ratio = (toxic_count / len(comments)) if comments else 0.0

            _json_response(self, {
                "username": username,
                "comments": comments,
                "stats": {
                    "total_captured": len(comments),
                    "toxicity_ratio": toxicity_ratio,
                    "top_keywords": top_keywords
                }
            })
        except Exception as exc:
            log.error(f"[CommentsEndpoint] Error sirviendo comentarios para {username}: {exc}")
            _json_response(self, {"error": str(exc)}, 500)


    def _serve_tiktok_audio_transcript(self):
        """
        GET /v1/tiktok/audio_transcript?user=HANDLE
        Retorna las líneas de transcripción de audio del directo en tiempo real.
        """
        params = _parse_qs(self.path)
        username = params.get("user", "").lstrip("@")
        if not username:
            _json_response(self, {"error": "Se requiere ?user=HANDLE"}, 400)
            return
        try:
            from core.tiktok_radar import get_radar
            lines = get_radar().get_audio_transcript(username)
            _json_response(self, {
                "username": username,
                "transcript": lines,
                "total": len(lines),
                "note": "Transcripción en tiempo real via Whisper/ffmpeg."
            })
        except Exception as exc:
            log.error(f"[AudioTranscriptAPI] Error para @{username}: {exc}")
            _json_response(self, {"error": str(exc)}, 500)

    def _serve_tiktok_psychological_profile(self):
        """
        GET /v1/tiktok/psychological_profile?user=HANDLE
        Analiza el audio transcrito + comentarios del chat y genera un perfil
        psicológico del streamer usando el LLM de Gravity AI.
        """
        params = _parse_qs(self.path)
        username = params.get("user", "").lstrip("@")
        if not username:
            _json_response(self, {"error": "Se requiere ?user=HANDLE"}, 400)
            return

        try:
            from core.tiktok_radar import get_radar
            radar = get_radar()

            # Recopilar datos de ambas fuentes
            audio_lines = radar.get_audio_transcript(username)
            chat_comments = radar.get_comments(username)

            if not audio_lines and not chat_comments:
                _json_response(self, {
                    "username": username,
                    "error": "No hay datos de audio ni chat disponibles aún. Asegúrate de que el canal esté en vivo.",
                    "profile": None
                }, 404)
                return

            # Construir contexto de análisis
            audio_text = "\n".join([f"[{l.get('speaker', 'Streamer')}]: {l['text']}" for l in audio_lines[-30:]]) if audio_lines else "(sin audio disponible)"
            chat_text = "\n".join([f"@{c.get('user_id','?')}: {c.get('text','')}" for c in chat_comments[-30:]]) if chat_comments else "(sin chat disponible)"

            prompt = f"""
            Analiza los siguientes datos en tiempo real de un directo en TikTok Live.

            DIÁLOGO DETECTADO (con identificación automática de hablantes):
            {audio_text}

            LO QUE DICE EL CHAT:
            {chat_text}

            Genera un perfil psicológico-conductual forense estructurado en JSON con los siguientes campos:
            {{
              "archetype": "(Educador|Entretenedor|Líder|Manipulador|Activista|Vendedor|etc.)",
              "dominant_emotion": "(confianza|ira|alegría|ansiedad|entusiasmo|frustración|etc.)",
              "stress_level": 0.0-1.0,
              "sarcasm_index": 0.0-1.0,
              "vulnerability_score": 0.0-1.0,
              "engagement_drive": "(altruista|egoísta|mixto)",
              "communication_style": "(asertivo|pasivo|agresivo|didáctico|humoristico)",
              "cognitive_distortions": ["lista de distorsiones cognitivas o falacias lógicas observadas en su habla (ej. ad hominem, generalización apresurada, victimización, falacia del espantapájaros)"],
              "persuasion_techniques": ["lista de técnicas de persuasión o manipulación identificadas (ej. gaslighting, apelación a la emoción, proyección, encuadre defensivo)"],
              "defense_mechanisms": ["lista de mecanismos de defensa observados (ej. proyección, racionalización, negación, intelectualización, humor defensivo)"],
              "psychological_signals": ["lista de señales conductuales observadas en 3-5 puntos cortos"],
              "audience_congruence": "(alta|media|baja): descripción de si el chat apoya o contradice al streamer",
              "summary": "Resumen de 2-3 oraciones del perfil"
            }}

            Responde SOLO con el JSON, sin texto adicional.
            """

            from core.provider_manager import complete
            raw_response = complete(
                messages=[
                    {"role": "system", "content": "Eres un experto en psicología conductual y análisis de comportamiento en redes sociales. Respondes SOLO con JSON válido."},
                    {"role": "user", "content": prompt}
                ],
                task="any"
            )

            # Limpiar markdown si el LLM lo envolvió
            cleaned = raw_response.strip()
            if cleaned.startswith("```"):
                lines_clean = cleaned.splitlines()
                if lines_clean[0].startswith("```"):
                    lines_clean = lines_clean[1:]
                if lines_clean and lines_clean[-1].strip() == "```":
                    lines_clean = lines_clean[:-1]
                cleaned = "\n".join(lines_clean).strip()

            try:
                profile = json.loads(cleaned)
                # Guardar en la Memoria Estratégica Global de Gravity AI
                try:
                    from core.strategic_memory import upsert_pattern
                    upsert_pattern(f"tiktok:profile:{username}", json.dumps(profile, ensure_ascii=False))
                except Exception as mem_err:
                    log.warning(f"[PsychProfile] Fallo guardando en Memoria Estratégica: {mem_err}")
            except Exception:
                profile = {"raw_analysis": cleaned}

            _json_response(self, {
                "username": username,
                "profile": profile,
                "data_points": {
                    "audio_lines_analyzed": len(audio_lines),
                    "chat_comments_analyzed": len(chat_comments)
                }
            })

        except Exception as exc:
            log.error(f"[PsychProfile] Error generando perfil para @{username}: {exc}")
            _json_response(self, {"error": str(exc)}, 500)

    def _serve_tiktok_send_chat(self):
        """
        POST /v1/tiktok/send_chat
        Envía un mensaje de chat a la transmisión en vivo utilizando el webcast API y la sessionid.
        """
        body = _read_json_body(self)
        if not body:
            _json_response(self, {"error": "Cuerpo JSON inválido o ausente"}, 400)
            return

        username = body.get("user", "").lstrip("@")
        message = body.get("message", "")
        session_id = body.get("session_id", "")

        if not username or not message:
            _json_response(self, {"error": "Se requieren los campos 'user' y 'message'"}, 400)
            return

        try:
            # 1. Obtener room_id activo del canal
            radar = _get_radar()
            status = radar.get_status()
            room_id = None
            for channel in status.get("channels", []):
                if channel["username"].lower() == username.lower():
                    room_id = channel.get("room_id")
                    break

            if not room_id:
                _json_response(self, {"error": f"No se pudo encontrar un Room ID activo para @{username}. Asegúrate de que el canal esté en vivo y monitoreado."}, 400)
                return

            # 2. Reconstruir todos los cookies desde cookies.txt para evitar el 403 Forbidden
            cookie_list = []
            cookies_path = os.path.join(_BASE_DIR, "cookies.txt")
            if os.path.exists(cookies_path):
                try:
                    with open(cookies_path, "r", encoding="utf-8", errors="ignore") as f:
                        for line in f:
                            if line.startswith("#") or not line.strip():
                                continue
                            parts = line.strip().split("\t")
                            if len(parts) >= 7:
                                name = parts[5]
                                value = parts[6]
                                # Si pasaron un session_id en el payload, usar ese en lugar del de cookies.txt
                                if name == "sessionid" and session_id:
                                    value = session_id
                                if name == "sessionid_ss" and session_id:
                                    value = session_id
                                cookie_list.append(f"{name}={value}")
                except Exception as ce:
                    log.warning(f"[SendChat] Error leyendo cookies.txt: {ce}")

            # Si no leyó nada de cookies.txt pero pasaron session_id, armar lo mínimo
            if not cookie_list and session_id:
                cookie_list.append(f"sessionid={session_id}")
                cookie_list.append(f"sessionid_ss={session_id}")

            # Asegurar que se añada session_id si no estaba en cookies.txt pero fue enviado en el body
            has_sessionid = any(c.startswith("sessionid=") for c in cookie_list)
            if not has_sessionid and session_id:
                cookie_list.append(f"sessionid={session_id}")
                cookie_list.append(f"sessionid_ss={session_id}")

            cookie_str = "; ".join(cookie_list)

            # 3. Construir petición POST para webcast.tiktok.com
            import urllib.request
            import urllib.parse
            import json

            url = "https://webcast.tiktok.com/webcast/room/chat/"
            query_params = {
                "aid": "1988",
                "app_name": "tiktok_web",
                "device_platform": "web",
                "room_id": room_id
            }
            full_url = f"{url}?{urllib.parse.urlencode(query_params)}"

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36",
                "Referer": f"https://www.tiktok.com/@{username}/live",
                "Origin": "https://www.tiktok.com",
                "Cookie": cookie_str,
                "Content-Type": "application/x-www-form-urlencoded"
            }

            post_data = urllib.parse.urlencode({"content": message}).encode("utf-8")
            req = urllib.request.Request(full_url, data=post_data, headers=headers, method="POST")

            with urllib.request.urlopen(req) as response:
                res_body = response.read().decode("utf-8", errors="ignore").strip()
                if not res_body:
                    # TikTok a veces responde con body vacío en peticiones exitosas
                    _json_response(self, {"success": True, "note": "Mensaje enviado (TikTok retornó cuerpo vacío)"})
                    return

                try:
                    res_data = json.loads(res_body)
                    status_code = res_data.get("status_code", 0)
                    if status_code != 0:
                        err_msg = res_data.get("data", {}).get("prompts", "Error de envío (verifique los permisos o si la sesión expiró).")
                        _json_response(self, {"error": f"TikTok: {err_msg} (código={status_code})", "raw": res_data}, 400)
                    else:
                        _json_response(self, {"success": True, "data": res_data})
                except Exception:
                    # Si no es JSON pero responde con 200, asumir éxito
                    _json_response(self, {"success": True, "raw_body": res_body})

        except Exception as exc:
            log.error(f"[SendChat] Error enviando mensaje a @{username}: {exc}")
            _json_response(self, {"error": str(exc)}, 500)

    def _handle_post_tiktok(self) -> bool:
        """
        Dispatcher POST para el módulo GTLIS.
        Retorna True si manejó la ruta, False si no aplica.
        Sigue el mismo patrón de _handle_post_chat(), _handle_post_system(), etc.
        """
        path = self.path.split("?")[0]
        _POST_ROUTES = {
            "/v1/tiktok/watch":     self._serve_tiktok_watch,
            "/v1/tiktok/unwatch":   self._serve_tiktok_unwatch,
            "/v1/tiktok/analyze":   self._serve_tiktok_analyze,
            "/v1/tiktok/geo":       self._serve_tiktok_geo,
            "/v1/tiktok/send_chat": self._serve_tiktok_send_chat,
        }
        handler = _POST_ROUTES.get(path)
        if handler:
            handler()
            return True
        return False

