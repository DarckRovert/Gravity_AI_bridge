import json
import time
import uuid
import os
import yaml
from core import provider_manager
from core.audit_log import audit_logger
from core.metrics import record_request, record_tokens, record_latency, record_error
from core.logger import log
from core.rate_limiter import check_access
from core.reasoning_stripper import ReasoningStripper


class PostChatMixin:
    def _handle_post_chat(self):
        if self.path == "/v1/keys":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(length)) if length else {}
                provider = data.get("provider", "").strip().lower()
                api_key = data.get("api_key", "").strip()
                if not provider or not api_key:
                    self.send_response(400)
                    self.send_header("Content-Type", "application/json")
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(
                        json.dumps(
                            {"error": "provider y api_key son requeridos"}
                        ).encode()
                    )
                    return True
                from core.key_manager import KeyManager

                KeyManager.set_key(provider, api_key)
                body = json.dumps(
                    {
                        "ok": True,
                        "provider": provider,
                        "masked": KeyManager.mask(provider),
                    }
                ).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return True

        # /v1/cost/limit — Actualizar límite diario de gasto
        if self.path == "/v1/model/lock":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(length)) if length else {}
                provider = data.get("provider", "").strip()
                model = data.get("model", "").strip()
                lock = bool(data.get("lock", True))

                BASE_DIR = os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
                settings_path = os.path.join(BASE_DIR, "_settings.json")

                with open(settings_path, "r", encoding="utf-8") as f:
                    settings = json.load(f)

                if not lock:
                    settings["model_locked"] = False
                    settings.pop("locked_provider", None)
                    settings.pop("locked_model", None)
                else:
                    if not provider or not model:
                        self.send_response(400)
                        self.send_header("Content-Type", "application/json")
                        self._send_cors()
                        self.end_headers()
                        self.wfile.write(
                            json.dumps(
                                {
                                    "error": "provider y model son requeridos para bloquear"
                                }
                            ).encode()
                        )
                        return True
                    settings["model_locked"] = True
                    settings["locked_provider"] = provider
                    settings["locked_model"] = model

                with open(settings_path, "w", encoding="utf-8") as f:
                    json.dump(settings, f, indent=4, ensure_ascii=False)

                body = json.dumps(
                    {
                        "ok": True,
                        "model_locked": settings["model_locked"],
                        "locked_provider": settings.get("locked_provider"),
                        "locked_model": settings.get("locked_model"),
                    }
                ).encode()

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return True

        # /v1/universal/config — Guardar configuración del proveedor Universal AI
        if self.path == "/v1/gravity/chat":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(length)) if length else {}
                messages_in = data.get("messages", [])
                stream_mode = data.get("stream", True)

                user_msg = ""
                user_msg_idx = -1
                for i in range(len(messages_in) - 1, -1, -1):
                    if messages_in[i].get("role") == "user":
                        user_msg = messages_in[i].get("content", "")
                        user_msg_idx = i
                        break

                # Inyección de scraping web en tiempo real para el Chat
                if user_msg_idx != -1:
                    import re

                    urls = re.findall(r"(https?://[^\s)\]]+)", user_msg)
                    if urls:
                        try:
                            from core.firecrawl_scraper import scrape_url

                            _base_dir_scrape = os.path.dirname(
                                os.path.dirname(
                                    os.path.dirname(os.path.abspath(__file__))
                                )
                            )
                            api_key = ""
                            try:
                                with open(
                                    os.path.join(_base_dir_scrape, "config.yaml"),
                                    "r",
                                    encoding="utf-8",
                                ) as f:
                                    api_key = yaml.safe_load(f).get(
                                        "firecrawl_api_key", ""
                                    )
                            except:
                                pass

                            for url in urls[:1]:
                                scrape_res = scrape_url(url, api_key=api_key)
                                if scrape_res.get("ok"):
                                    scraped_text = scrape_res.get("content", "")[:6000]
                                    messages_in[user_msg_idx]["content"] = (
                                        user_msg.replace(
                                            url,
                                            f"[{url} - CONTENIDO WEB EXTRAÍDO:\n{scraped_text}\n]",
                                        )
                                    )
                                    user_msg = messages_in[user_msg_idx]["content"]
                        except Exception:
                            pass

                # Detectar comandos del sistema
                from core.gravity_brain import (
                    parse_chat_commands,
                    execute_system_command,
                    build_gravity_system_prompt,
                )
                from core import data_guardian

                cmd_info = parse_chat_commands(user_msg)
                if cmd_info:
                    # Ejecutar el comando del sistema
                    cmd_result = execute_system_command(cmd_info)
                    feedback = cmd_info.get("user_feedback", "")
                    result_text = cmd_result.get("result_text", "Sin resultado")
                    ok = cmd_result.get("ok", False)
                    icon = "✓" if ok else "✗"

                    # Construir respuesta con resultado del comando
                    response_content = (
                        f"**{icon} {feedback}**\n\n"
                        f"Acción ejecutada: `{cmd_info.get('api_action', cmd_info.get('command'))}`\n\n"
                        f"```\n{result_text}\n```"
                    )

                    if stream_mode:
                        chat_id = f"chatcmpl-gravity-{uuid.uuid4().hex[:10]}"
                        self.send_response(200)
                        self.send_header("Content-Type", "text/event-stream")
                        self.send_header("Cache-Control", "no-cache")
                        self._send_cors()
                        self.end_headers()
                        chunk = {
                            "id": chat_id,
                            "object": "chat.completion.chunk",
                            "model": "gravity-brain-v16",
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {"content": response_content},
                                    "finish_reason": None,
                                }
                            ],
                        }
                        self.wfile.write(
                            f"data: {json.dumps(chunk)}\n\n".encode("utf-8")
                        )
                        final = {
                            "id": chat_id,
                            "object": "chat.completion.chunk",
                            "model": "gravity-brain-v16",
                            "choices": [
                                {"index": 0, "delta": {}, "finish_reason": "stop"}
                            ],
                        }
                        self.wfile.write(
                            f"data: {json.dumps(final)}\n\n".encode("utf-8")
                        )
                        self.wfile.write(b"data: [DONE]\n\n")
                        self.wfile.flush()
                    else:
                        body = json.dumps(
                            {
                                "id": f"chatcmpl-gravity-{uuid.uuid4().hex[:10]}",
                                "object": "chat.completion",
                                "model": "gravity-brain-v16",
                                "choices": [
                                    {
                                        "index": 0,
                                        "message": {
                                            "role": "assistant",
                                            "content": response_content,
                                        },
                                        "finish_reason": "stop",
                                    }
                                ],
                                "usage": {
                                    "prompt_tokens": 0,
                                    "completion_tokens": 0,
                                    "total_tokens": 0,
                                },
                            }
                        ).encode("utf-8")
                        self.send_response(200)
                        self.send_header("Content-Type", "application/json")
                        self._send_cors()
                        self.end_headers()
                        self.wfile.write(body)
                    return True

                # No es un comando — chat normal con conciencia sistémica inyectada
                _base_dir_brain = os.path.dirname(
                    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                )
                kb_data_brain = {}
                try:
                    kb_data_brain, _ = data_guardian.load_knowledge(
                        os.path.join(_base_dir_brain, "_knowledge.json")
                    )
                except Exception:
                    pass

                extra_rules = kb_data_brain.get("persistent_rules", [])
                system_prompt = build_gravity_system_prompt(
                    extra_rules=extra_rules if extra_rules else None
                )

                # Insertar system prompt con conciencia sistémica
                messages_out = [m for m in messages_in if m.get("role") != "system"]
                messages_out.insert(0, {"role": "system", "content": system_prompt})

                # Inyección RAG si está activa
                try:
                    settings_brain = {}
                    sp = os.path.join(_base_dir_brain, "_settings.json")
                    with open(sp, "r", encoding="utf-8") as _sf:
                        settings_brain = json.load(_sf)
                    if settings_brain.get("rag_enabled", False) and user_msg:
                        from rag.retriever import RAGRetriever

                        rag_ctx = RAGRetriever.retrieve_as_context(
                            user_msg[:500], top_k=3
                        )
                        if rag_ctx:
                            if messages_out and messages_out[0].get("role") == "system":
                                messages_out[0][
                                    "content"
                                ] += (
                                    f"\n\n[CONTEXTO RAG/CONOCIMIENTO EXTRA]:\n{rag_ctx}"
                                )
                            else:
                                messages_out.insert(
                                    0, {"role": "system", "content": rag_ctx}
                                )
                            log.info("[GravityChat] RAG inyectado")
                except Exception:
                    pass

                # Obtener proveedor activo
                from core import provider_manager as _pm

                best_p, best_m = _pm.get_best()
                if not best_p:
                    error_body = json.dumps(
                        {
                            "error": "No hay proveedor de IA disponible. Inicia un motor local o configura una API key."
                        }
                    ).encode()
                    self.send_response(503)
                    self.send_header("Content-Type", "application/json")
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(error_body)
                    return True

                options = {
                    k: data[k]
                    for k in ("temperature", "top_p", "max_tokens")
                    if k in data
                }
                stripper = ReasoningStripper()
                chat_id = f"chatcmpl-gravity-{uuid.uuid4().hex[:10]}"

                if stream_mode:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.send_header("Cache-Control", "no-cache")
                    self._send_cors()
                    self.end_headers()
                    for chunk_text in _pm.stream(
                        messages_out,
                        model=best_m,
                        provider=best_p.name,
                        options=options,
                    ):
                        if not chunk_text:
                            continue
                        clean = stripper.process_chunk(chunk_text)
                        if not clean:
                            continue
                        chunk = {
                            "id": chat_id,
                            "object": "chat.completion.chunk",
                            "model": best_m,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {"content": clean},
                                    "finish_reason": None,
                                }
                            ],
                        }
                        try:
                            self.wfile.write(
                                f"data: {json.dumps(chunk)}\n\n".encode("utf-8")
                            )
                            self.wfile.flush()
                        except Exception:
                            break
                    final = {
                        "id": chat_id,
                        "object": "chat.completion.chunk",
                        "model": best_m,
                        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                    }
                    try:
                        self.wfile.write(
                            f"data: {json.dumps(final)}\n\n".encode("utf-8")
                        )
                        self.wfile.write(b"data: [DONE]\n\n")
                        self.wfile.flush()
                    except Exception:
                        pass
                else:
                    raw = _pm.complete(
                        messages_out,
                        model=best_m,
                        provider=best_p.name,
                        options=options,
                    )
                    full = stripper.process_chunk(raw)
                    body = json.dumps(
                        {
                            "id": chat_id,
                            "object": "chat.completion",
                            "model": best_m,
                            "choices": [
                                {
                                    "index": 0,
                                    "message": {"role": "assistant", "content": full},
                                    "finish_reason": "stop",
                                }
                            ],
                        }
                    ).encode("utf-8")
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(body)
            except Exception as e:
                log.error(f"[GravityChat] Error: {e}", exc_info=True)
                try:
                    body = json.dumps({"error": str(e)}).encode("utf-8")
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json")
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(body)
                except Exception:
                    pass
            return True

        # Rate limiting
        if self.path == "/v1/chat/completions":
            ip = self.client_address[0]
            auth_hdr = self.headers.get("Authorization", "")
            api_key = auth_hdr.split(" ")[-1] if " " in auth_hdr else auth_hdr
            allowed, reason = check_access(ip, api_key)
            if not allowed:
                self.send_response(429)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": reason}).encode())
                record_error("rate_limit")
                return True

            try:
                content_length = int(self.headers.get("Content-Length", 0))
                post_data = self.rfile.read(content_length)
                payload = json.loads(post_data.decode("utf-8"))
                messages = payload.get("messages", [])
                req_model = payload.get("model", "gravity-bridge-auto")
                is_streaming = payload.get("stream", True)
                options = {
                    k: payload[k]
                    for k in ("temperature", "top_p", "max_tokens", "stop")
                    if k in payload
                }

                # ── Auto-inyección de Personalidad (Knowledge Base) ──
                if not any(m.get("role") == "system" for m in messages):
                    try:
                        from core import data_guardian

                        _base_dir = os.path.dirname(
                            os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        )
                        kb_data, _ = data_guardian.load_knowledge(
                            os.path.join(_base_dir, "_knowledge.json")
                        )
                        _sys_prompt = (
                            "Eres Gravity AI V16.0 PRO, Auditor Senior. "
                            "PROTOCOLO: Lógica interna en inglés. Salida final en español estrictamente. "
                            "Sin rellenos conversacionales. Solo hechos técnicos fríos. Resolución directa."
                        )
                        if (
                            kb_data
                            and "persistent_rules" in kb_data
                            and kb_data["persistent_rules"]
                        ):
                            _sys_prompt += "\n\nCONOCIMIENTO CRÍTICO:\n" + "\n".join(
                                kb_data["persistent_rules"]
                            )
                        messages.insert(0, {"role": "system", "content": _sys_prompt})
                    except Exception as e:
                        log.error(f"Error cargando personalidad para el bridge: {e}")

                # ── Inyección RAG (si está activada en _settings.json) ──
                try:
                    _base_dir_rag = os.path.dirname(
                        os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    )
                    _settings_path = os.path.join(_base_dir_rag, "_settings.json")
                    with open(_settings_path, "r", encoding="utf-8") as _sf:
                        _rag_enabled = json.load(_sf).get("rag_enabled", False)
                    if _rag_enabled:
                        # Extraer la última query del usuario para la búsqueda
                        _user_msgs = [m for m in messages if m.get("role") == "user"]
                        if _user_msgs:
                            _query = _user_msgs[-1].get("content", "")[:500]
                            from rag.retriever import RAGRetriever

                            _rag_context = RAGRetriever.retrieve_as_context(
                                _query, top_k=4
                            )
                            if _rag_context:
                                if messages and messages[0].get("role") == "system":
                                    messages[0][
                                        "content"
                                    ] += f"\n\n[CONTEXTO RAG/CONOCIMIENTO EXTRA]:\n{_rag_context}"
                                else:
                                    messages.insert(
                                        0, {"role": "system", "content": _rag_context}
                                    )
                                log.info(
                                    f"[RAG] Contexto inyectado ({len(_rag_context)} chars) para query: {_query[:60]}..."
                                )
                except Exception as _rag_err:
                    log.debug(
                        f"[RAG] Skip — {_rag_err}"
                    )  # Silencioso si RAG no está disponible

                target_prov = None
                target_mod = req_model
                if req_model == "gravity-bridge-auto":
                    bp, bm = provider_manager.get_best()
                    if bp:
                        target_prov, target_mod = bp.name, bm
                else:
                    for r in provider_manager.scan_all():
                        if r.is_healthy and any(
                            m["name"] == req_model for m in r.models
                        ):
                            target_prov = r.name
                            break

                if not target_prov:
                    self.send_response(503)
                    self.end_headers()
                    self.wfile.write(b'{"error":"No provider available."}')
                    record_error("no_provider")
                    return True

                record_request(target_prov, target_mod)
                chat_id = f"chatcmpl-{uuid.uuid4().hex[:12]}"
                start_time = time.time()
                input_chars = sum(len(m.get("content", "")) for m in messages)
                input_tokens = input_chars // 4
                record_tokens("input", target_prov, target_mod, input_tokens)
                stripper = ReasoningStripper()

                if is_streaming:
                    self.send_response(200)
                    self.send_header("Content-Type", "text/event-stream")
                    self.send_header("Cache-Control", "no-cache")
                    self._send_cors()
                    self.end_headers()
                    output_chars = 0
                    for chunk_text in provider_manager.stream(
                        messages,
                        model=target_mod,
                        provider=target_prov,
                        options=options,
                    ):
                        if not chunk_text:
                            continue
                        clean = stripper.process_chunk(chunk_text)
                        if not clean:
                            continue
                        output_chars += len(clean)
                        chunk = {
                            "id": chat_id,
                            "object": "chat.completion.chunk",
                            "model": target_mod,
                            "choices": [
                                {
                                    "index": 0,
                                    "delta": {"content": clean},
                                    "finish_reason": None,
                                }
                            ],
                        }
                        try:
                            self.wfile.write(
                                f"data: {json.dumps(chunk)}\n\n".encode("utf-8")
                            )
                            self.wfile.flush()
                        except Exception as write_err:
                            log.debug(
                                f"[Streaming] Socket cerrado durante escritura: {write_err}"
                            )
                            break
                    # Final [DONE]
                    final = {
                        "id": chat_id,
                        "object": "chat.completion.chunk",
                        "model": target_mod,
                        "choices": [{"index": 0, "delta": {}, "finish_reason": "stop"}],
                    }
                    try:
                        self.wfile.write(
                            f"data: {json.dumps(final)}\n\n".encode("utf-8")
                        )
                        self.wfile.write(b"data: [DONE]\n\n")
                        self.wfile.flush()
                    except Exception:
                        pass
                    output_tokens = output_chars // 4
                    record_tokens("output", target_prov, target_mod, output_tokens)
                else:
                    raw_text = provider_manager.complete(
                        messages,
                        model=target_mod,
                        provider=target_prov,
                        options=options,
                    )
                    full_text = stripper.process_chunk(raw_text)
                    output_chars = len(full_text)
                    output_tokens = output_chars // 4
                    record_tokens("output", target_prov, target_mod, output_tokens)
                    resp = {
                        "id": chat_id,
                        "object": "chat.completion",
                        "model": target_mod,
                        "choices": [
                            {
                                "index": 0,
                                "message": {"role": "assistant", "content": full_text},
                                "finish_reason": "stop",
                            }
                        ],
                        "usage": {
                            "prompt_tokens": input_tokens,
                            "completion_tokens": output_tokens,
                            "total_tokens": input_tokens + output_tokens,
                        },
                    }
                    body = json.dumps(resp).encode()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.send_header("Content-Length", str(len(body)))
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(body)

                elapsed = time.time() - start_time
                record_latency(target_prov, target_mod, elapsed)
                from core.cost_tracker import CostTracker

                plugin = provider_manager.get_plugin(target_prov)
                usd = 0.0
                if plugin and getattr(plugin, "category", "") == "cloud":
                    usd = CostTracker.estimate(
                        target_prov, target_mod, input_chars, output_chars
                    )
                    CostTracker.record(
                        target_prov, target_mod, input_tokens, output_tokens, usd
                    )
                audit_logger.record(
                    chat_id,
                    target_prov,
                    target_mod,
                    input_tokens,
                    output_tokens,
                    usd,
                    elapsed * 1000,
                )

            except Exception as e:
                log.error(f"Error in POST /v1/chat/completions: {e}", exc_info=True)
                record_error("internal_error")
                try:
                    body = json.dumps({"error": str(e)}).encode("utf-8")
                    self.send_response(500)
                    self.send_header("Content-Type", "application/json; charset=utf-8")
                    self.send_header("Content-Length", str(len(body)))
                    self.end_headers()
                    self.wfile.write(body)
                except Exception:
                    pass
            return True

        # ── V13.0 Monetization Hub — POST handlers ────────────────────────────

        # /v1/language/clone — Clonar un job a otros idiomas
        if self.path == "/v1/language/clone":
            try:
                length = int(self.headers.get("Content-Length", 0))
                data = json.loads(self.rfile.read(length)) if length else {}
                job_id = data.get("job_id")
                langs = data.get("languages", None)
                if not job_id:
                    self.send_response(400)
                    self._send_cors()
                    self.end_headers()
                    self.wfile.write(json.dumps({"error": "job_id requerido"}).encode())
                    return
                from core.language_cloner import clone_job_async

                clone_job_async(int(job_id), langs)
                body = json.dumps(
                    {
                        "ok": True,
                        "job_id": job_id,
                        "message": "Clonación iniciada en background.",
                        "languages": langs,
                    }
                ).encode()
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self._send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception as e:
                self.send_response(500)
                self._send_cors()
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return True

        # /v1/affiliates/program/add — Agregar programa de afiliado a un niche
        return False
