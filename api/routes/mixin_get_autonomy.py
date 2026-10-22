"""
╔══════════════════════════════════════════════════════════════════════════════╗
║     GRAVITY AI — GET ROUTES MIXIN: AUTONOMY & REVENUE [Modular Sub-Router]   ║
║          Autonomy Engine, Auto-Reflection, Bounties, Factory & SSE Stream    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import re
import json
import glob
import datetime
import urllib.parse


class GetAutonomyMixin:
    """Sub-mixin especializado en rutas GET para Autonomía, Bounties, Fábrica y SSE."""

    # ── Bounty Hunter ─────────────────────────────────────────────────────────
    def _serve_bounties(self):
        """GET /v1/bounties — Extrae y parsea los micro-trabajos de BOUNTIES_ENCONTRADOS.md"""
        try:
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            file_path = os.path.join(BASE_DIR, "BOUNTIES_ENCONTRADOS.md")
            _app_data = os.path.join(
                os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")), 
                "Gravity", 
                "Databases"
            )
            actions_path = os.path.join(_app_data, ".bounty_actions.json")
            settings_path = os.path.join(BASE_DIR, "_settings.json")

            seen_urls = set()
            if os.path.exists(actions_path):
                try:
                    with open(actions_path, "r", encoding="utf-8") as f:
                        actions = json.load(f)
                        seen_urls = set(actions.keys())
                except Exception:
                    pass

            bounty_profile = "Eres un desarrollador experto buscando trabajo freelance."
            if os.path.exists(settings_path):
                try:
                    with open(settings_path, "r", encoding="utf-8") as f:
                        bounty_profile = json.load(f).get("bounty_profile", bounty_profile)
                except Exception:
                    pass

            bounties = []
            if os.path.exists(file_path):
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()

                blocks = re.split(r"(?=\n## 🎯 Oportunidad:|\n\*\*Título:\*\*)", "\n" + content)
                for block in reversed(blocks):
                    block = block.strip()
                    if not block:
                        continue

                    title_match = re.search(r"## 🎯 Oportunidad:\s+(.*)", block)
                    if title_match:
                        title = title_match.group(1).strip()
                        url_match = re.search(r"\*\*Enlace original:\*\*\s+(.*)", block)
                        url = url_match.group(1).strip() if url_match else ""
                    else:
                        title_match = re.search(r"\*\*Título:\*\*\s+\[(.*?)\]\((.*?)\)", block)
                        if title_match:
                            title = title_match.group(1).strip()
                            url = title_match.group(2).strip()
                        else:
                            continue

                    if url and url in seen_urls:
                        continue

                    platform_match = re.search(r"\*\*Plataforma:\*\*\s+(.*?)\s+\|", block)
                    if not platform_match:
                        platform_match = re.search(r"\*\*Plataforma:\*\*\s+(.*)", block)

                    date_match = re.search(r"\*\*Detectado:\*\*\s+(.*)", block)
                    if not date_match:
                        date_match = re.search(r"\*\*Fecha:\*\*\s+(.*)", block)

                    desc_match = re.search(r"### Descripción Original del Cliente\n```text\n(.*?)\n```", block, re.DOTALL)
                    if not desc_match:
                        desc_match = re.search(r"\*\*Descripción Original:\*\*\n(.*?)(?=\*\*Propuesta de IA:\*\*|\Z)", block, re.DOTALL)

                    prop_match = re.search(r"### Propuesta de Venta Generada por IA \(Copiar y Enviar\)\n(.*?)(?:\n---|\Z)", block, re.DOTALL)
                    if not prop_match:
                        prop_match = re.search(r"\*\*Propuesta de IA:\*\*\n(.*)", block, re.DOTALL)

                    proposal_text = prop_match.group(1).strip() if prop_match else ""
                    if proposal_text.startswith(">"):
                        proposal_text = "\n".join([line.lstrip("> ") for line in proposal_text.split("\n")])

                    proposal_text = re.sub(r"<think>.*?</think>", "", proposal_text, flags=re.DOTALL).strip()

                    bounties.append({
                        "title": title,
                        "url": url,
                        "platform": platform_match.group(1).strip() if platform_match else "Unknown",
                        "date": date_match.group(1).strip() if date_match else "",
                        "description": desc_match.group(1).strip() if desc_match else "",
                        "proposal": proposal_text,
                    })

            bounties = bounties[:50]
            body = json.dumps(
                {"bounties": bounties, "count": len(bounties), "bounty_profile": bounty_profile},
                ensure_ascii=False,
            ).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self._send_cors()
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _serve_bounties_status(self):
        """GET /v1/bounties/status — Estado en vivo del daemon Bounty Hunter."""
        try:
            from core import bounty_hunter
            data = bounty_hunter.get_status()
            body = json.dumps(data).encode("utf-8")
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

    # ── Software Factory ──────────────────────────────────────────────────────
    def _serve_factory_list(self):
        try:
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            entregables_dir = os.path.join(BASE_DIR, "_entregables")
            os.makedirs(entregables_dir, exist_ok=True)

            zips = glob.glob(os.path.join(entregables_dir, "*.zip"))
            deliverables = []
            for z in zips:
                st = os.stat(z)
                size_kb = st.st_size / 1024
                size_str = f"{size_kb:.1f} KB" if size_kb < 1024 else f"{size_kb/1024:.2f} MB"
                deliverables.append({
                    "filename": os.path.basename(z),
                    "size": size_str,
                    "created_at": datetime.datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                    "mtime": st.st_mtime,
                })

            deliverables.sort(key=lambda x: x["mtime"], reverse=True)
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self._send_cors()
            self.end_headers()
            self.wfile.write(json.dumps({"deliverables": deliverables}, ensure_ascii=False).encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self._send_cors()
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _serve_factory_download(self):
        try:
            filename = self.path[len("/v1/factory/download/") :]
            filename = urllib.parse.unquote(filename)
            filename = os.path.basename(filename)

            BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            filepath = os.path.join(BASE_DIR, "_entregables", filename)

            if not os.path.isfile(filepath):
                self.send_response(404)
                self.end_headers()
                return

            with open(filepath, "rb") as f:
                content = f.read()

            self.send_response(200)
            self.send_header("Content-Type", "application/zip")
            self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.send_header("Content-Length", str(len(content)))
            self._send_cors()
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_response(500)
            self._send_cors()
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    # ── V16.0 PRO Autonomous Edition ────────────────────────────────────────────
    def _serve_autonomy_status(self):
        """GET /v1/autonomy/status — Estado completo del Autonomy Engine."""
        try:
            from core.autonomy_engine import get_state
            from core.self_reflection import get_state as refl_state, _count_pending_patches

            ae = get_state()
            rs = refl_state()
            payload = {
                "autonomy_engine": ae,
                "self_reflection": {**rs, "patches_pending": _count_pending_patches()},
                "ok": True,
            }
            body = json.dumps(payload, indent=2, ensure_ascii=False).encode("utf-8")
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

    def _serve_autonomy_decisions(self):
        """GET /v1/autonomy/decisions — Historial de decisiones estratégicas."""
        try:
            from core.strategic_memory import get_recent_decisions, get_summary

            decisions = get_recent_decisions(50)
            summary = get_summary(30)
            body = json.dumps(
                {"decisions": decisions, "summary": summary, "count": len(decisions)},
                indent=2, ensure_ascii=False, default=str,
            ).encode("utf-8")
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

    def _serve_autonomy_rules(self):
        """GET /v1/autonomy/rules — Reglas invariantes del sistema."""
        try:
            from core.autonomy_engine import (
                get_invariant_rules,
                AUTONOMY_DAILY_BUDGET_USD,
                DECISION_INTERVAL_H,
            )

            rules = get_invariant_rules()
            body = json.dumps(
                {
                    "invariant_rules": rules,
                    "daily_budget_usd": AUTONOMY_DAILY_BUDGET_USD,
                    "decision_interval_hours": DECISION_INTERVAL_H,
                    "ok": True,
                },
                indent=2, ensure_ascii=False,
            ).encode("utf-8")
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

    def _serve_reflection_report(self):
        """GET /v1/reflection/report — Último informe de auto-introspección."""
        try:
            from core.self_reflection import get_last_report

            report = get_last_report()
            if report is None:
                body = json.dumps({"ok": False, "message": "Aún no se ha ejecutado ningún ciclo de reflexión."}).encode("utf-8")
            else:
                body = json.dumps({"ok": True, "report": report}, indent=2, ensure_ascii=False, default=str).encode("utf-8")
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

    def _serve_reflection_patches(self):
        """GET /v1/reflection/patches — Parches de código pendientes de aprobación."""
        try:
            from core.self_reflection import get_pending_patches

            patches = get_pending_patches()
            body = json.dumps({"ok": True, "patches": patches, "count": len(patches)}, indent=2, ensure_ascii=False, default=str).encode("utf-8")
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

    def _serve_events_stream(self):
        """Endpoint SSE (Server-Sent Events) del Event Bus (Mythos Edition Phase 2)."""
        from core.event_bus import event_bus

        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "keep-alive")
        self._send_cors()
        self.end_headers()
        
        try:
            for item in event_bus.subscribe("global"):
                payload = json.dumps(item, ensure_ascii=False)
                self.wfile.write(f"data: {payload}\n\n".encode("utf-8"))
                self.wfile.flush()
        except Exception:
            pass
