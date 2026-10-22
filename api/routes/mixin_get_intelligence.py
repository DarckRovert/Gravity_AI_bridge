"""
╔══════════════════════════════════════════════════════════════════════════════╗
║     GRAVITY AI — GET ROUTES MIXIN: INTELLIGENCE & OSINT [Modular Sub-Router]  ║
║          Periodismo OSINT, Tinka Engine, NPU XDNA, Radar e Infiltrator       ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import sys
import json
import mimetypes
import urllib.parse
import urllib.request
from urllib.error import URLError


class GetIntelligenceMixin:
    """Sub-mixin especializado en rutas GET de Periodismo OSINT, Tinka y Sensores."""

    # ── Journalist Autonomous OSINT ─────────────────────────────────────────────
    def _serve_journalist_status(self):
        from api.routes.handlers.journalist_handler import handle_journalist_status
        handle_journalist_status(self)

    def _serve_journalist_log(self):
        from api.routes.handlers.journalist_handler import handle_journalist_log
        handle_journalist_log(self)

    def _serve_journalist_news(self):
        from api.routes.handlers.journalist_handler import handle_journalist_news
        handle_journalist_news(self)

    def _serve_journalist_images(self):
        path_clean = urllib.parse.unquote(self.path.split("?")[0])
        filename = os.path.basename(path_clean)
        filepath = os.path.join("f:\\gravity-news-portal\\public\\images", filename)
        
        if os.path.isfile(filepath):
            mime, _ = mimetypes.guess_type(filepath)
            mime = mime or "application/octet-stream"
            try:
                with open(filepath, "rb") as f:
                    body = f.read()
                self.send_response(200)
                self.send_header("Content-Type", mime)
                self.send_header("Content-Length", str(len(body)))
                self._send_cors()
                self.end_headers()
                self.wfile.write(body)
            except Exception:
                self.send_response(500)
                self.end_headers()
        else:
            self.send_response(404)
            self.end_headers()

    # ── La Tinka Engine ────────────────────────────────────────────────────────
    def _serve_tinka_status(self):
        try:
            BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            tools_dir = os.path.join(BASE, "tools")
            if tools_dir not in sys.path:
                sys.path.insert(0, tools_dir)
            from tinka_engine import TinkaEngine

            engine = TinkaEngine(os.path.join(BASE, "tinka_history.db"))
            body = json.dumps(engine.status(), indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _serve_tinka_analyze(self):
        try:
            BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            tools_dir = os.path.join(BASE, "tools")
            if tools_dir not in sys.path:
                sys.path.insert(0, tools_dir)
            from tinka_engine import TinkaEngine

            engine = TinkaEngine(os.path.join(BASE, "tinka_history.db"))
            body = json.dumps(engine.analyze_patterns(), indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _serve_tinka_predict(self):
        try:
            BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            tools_dir = os.path.join(BASE, "tools")
            if tools_dir not in sys.path:
                sys.path.insert(0, tools_dir)
            from tinka_engine import TinkaEngine

            engine = TinkaEngine(os.path.join(BASE, "tinka_history.db"))
            prediction = engine.predict_next_draw()
            body = json.dumps({"prediction": prediction}, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    def _serve_tinka_update(self):
        try:
            BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            tools_dir = os.path.join(BASE, "tools")
            if tools_dir not in sys.path:
                sys.path.insert(0, tools_dir)
            from tinka_engine import TinkaEngine

            params = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(self.path).query))
            force_dummy = params.get("dummy", "false").lower() == "true"

            engine = TinkaEngine(os.path.join(BASE, "tinka_history.db"))
            full_crawl = params.get("full", "false").lower() == "true"
            result = engine.update_database(
                full_crawl=full_crawl, force_dummy=force_dummy, num_dummy=100
            )
            body = json.dumps({"ok": True, "inserted": result}, indent=2).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self._send_cors()
            self.end_headers()
            self.wfile.write(body)
        except Exception as e:
            self.send_response(500)
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())

    # ── J.A.R.V.I.S y Radar ────────────────────────────────────────────────
    def _serve_jarvis_status(self):
        from api.routes.handlers.jarvis_handler import handle_jarvis_status
        handle_jarvis_status(self)

    def _serve_radar_status(self):
        from api.routes.handlers.radar_handler import handle_radar_status
        handle_radar_status(self)

    # ── NPU FastFlowLM AMD XDNA ───────────────────────────────────────────
    def _serve_npu_status(self):
        """Estado del NPU FastFlowLM AMD XDNA (puerto 52625)."""
        npu_detected = False
        try:
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SYSTEM\CurrentControlSet\Enum\PCI")
            npu_detected = any("VEN_1022" in winreg.EnumKey(key, i) and "DEV_1502" in winreg.EnumKey(key, i) for i in range(winreg.QueryInfoKey(key)[0]))
        except Exception:
            pass
        
        npu_msg = "NPU física AMD XDNA1 (Hawk Point) activa/detectada." if npu_detected else "No se detectó hardware NPU AMD compatible."
        url = "http://localhost:52625/v1/models"
        result = {"online": False, "models": [], "error": None, "port": 52625, "driver": "AMD XDNA"}
        try:
            with urllib.request.urlopen(url, timeout=2) as resp:
                data = json.loads(resp.read())
                result["online"] = True
                result["models"] = [m.get("id", "") for m in data.get("data", [])]
        except TimeoutError:
            result["error"] = f"FastFlowLM deshabilitado (XDNA2 requerido). {npu_msg}"
        except URLError as e:
            if isinstance(e.reason, TimeoutError) or "timed out" in str(e.reason).lower():
                result["error"] = f"FastFlowLM deshabilitado (XDNA2 requerido). {npu_msg}"
            elif "refused" in str(e.reason).lower() or "10061" in str(e.reason):
                result["error"] = f"FastFlowLM deshabilitado (XDNA2 requerido). {npu_msg}"
            else:
                result["error"] = f"Error de conexión: {e.reason}"
        except OSError as e:
            err = str(e)
            if "refused" in err.lower() or "10061" in err:
                result["error"] = f"FastFlowLM deshabilitado (XDNA2 requerido). {npu_msg}"
            elif "timeout" in err.lower() or "timed out" in err.lower():
                result["error"] = f"FastFlowLM deshabilitado (XDNA2 requerido). {npu_msg}"
            else:
                result["error"] = f"Error de conexión: {err}"
        except Exception as e:
            result["error"] = str(e)
            
        body = json.dumps(result, indent=2).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self._send_cors()
        self.end_headers()
        self.wfile.write(body)

    # ── Infiltrator ───────────────────────────────────────────────────────────
    def _serve_infiltrator_status(self):
        try:
            from core import infiltrator
            status = infiltrator.get_status()
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self._send_cors()
            self.end_headers()
            self.wfile.write(json.dumps(status, ensure_ascii=False).encode("utf-8"))
        except Exception as e:
            self.send_response(500)
            self._send_cors()
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())
