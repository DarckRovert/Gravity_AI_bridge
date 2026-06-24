"""
╔══════════════════════════════════════════════════════════════════════════════╗
║   GRAVITY AI — SWARM NODE V16.5 PRO                                          ║
║                                                                              ║
║   Agente esclavo ultra-ligero para escalado horizontal multinodo.            ║
║   Escucha peticiones HTTP del Bridge Principal y lanza procesos pesados      ║
║   (ej. Fooocus, V2V) localmente en la máquina secundaria.                    ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import os
import json
import subprocess
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging

try:
    import psutil

    _PSUTIL_OK = True
except ImportError:
    psutil = None
    _PSUTIL_OK = False

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] [SwarmNode] %(message)s"
)
log = logging.getLogger("gravity.swarm_node")

# Simple token para evitar ejecución no autorizada en la LAN
AUTH_TOKEN = "GRAVITY_SWARM_TOKEN_16"


class SwarmNodeHandler(BaseHTTPRequestHandler):
    def _send_response(self, code: int, data: dict):
        self.send_response(code)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_POST(self):
        auth_header = self.headers.get("Authorization", "")
        if auth_header != f"Bearer {AUTH_TOKEN}":
            self._send_response(401, {"success": False, "error": "Unauthorized"})
            return

        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            req = json.loads(post_data.decode("utf-8"))
        except json.JSONDecodeError:
            self._send_response(400, {"success": False, "error": "Invalid JSON"})
            return

        action = req.get("action")
        provider_name = req.get("provider_name", "")

        if self.path == "/v1/swarm/engine":
            if action == "start":
                path = req.get("executable_path")
                if not path or not os.path.exists(path):
                    self._send_response(
                        400,
                        {"success": False, "error": f"Invalid path on node: {path}"},
                    )
                    return
                res = self.start_engine(provider_name, path)
                self._send_response(200 if res["success"] else 500, res)
            elif action == "stop":
                res = self.stop_engine(provider_name)
                self._send_response(200 if res["success"] else 500, res)
            else:
                self._send_response(400, {"success": False, "error": "Unknown action"})
        else:
            self._send_response(404, {"success": False, "error": "Not found"})

    def start_engine(self, provider_name: str, path: str) -> dict:
        try:
            DETACHED_PROCESS = 0x00000008
            CREATE_NEW_CONSOLE = 0x00000010
            CREATE_NO_WINDOW = 0x08000000

            if (
                "v2v" in provider_name.lower()
                or "fooocus" in provider_name.lower()
                or "comfyui" in provider_name.lower()
            ):
                proc_flags = CREATE_NEW_CONSOLE
            else:
                proc_flags = DETACHED_PROCESS | CREATE_NO_WINDOW

            env = os.environ.copy()

            if path.endswith(".bat"):
                subprocess.Popen(
                    ["cmd.exe", "/c", path],
                    creationflags=proc_flags,
                    cwd=os.path.dirname(path),
                    env=env,
                    close_fds=True,
                )
            else:
                subprocess.Popen(
                    [path],
                    creationflags=proc_flags,
                    cwd=os.path.dirname(path),
                    env=env,
                    close_fds=True,
                )

            log.info(f"Started {provider_name} via {path}")
            return {
                "success": True,
                "message": f"{provider_name} iniciado en Swarm Node.",
            }
        except Exception as e:
            log.error(f"Failed to start {provider_name}: {e}")
            return {"success": False, "error": str(e)}

    def stop_engine(self, provider_name: str) -> dict:
        if not _PSUTIL_OK:
            return {"success": False, "error": "psutil no instalado en el nodo."}

        pn = provider_name.lower()
        targets = []
        if "lm studio" in pn:
            targets = ["LM Studio.exe", "lmstudioworker.exe"]
        elif "ollama" in pn:
            targets = ["ollama.exe", "ollama app.exe", "ollama_llama_server.exe"]
        elif "jan" in pn:
            targets = ["Jan.exe"]

        killed = 0
        for proc in psutil.process_iter(["name", "cmdline", "cwd"]):
            try:
                name = proc.info.get("name", "")
                if not name:
                    continue
                p_cwd = proc.info.get("cwd", "") or ""
                cmdline = " ".join(proc.info.get("cmdline", []) or [])

                if "fooocus" in pn and "python.exe" in name.lower():
                    if "launch.py" in cmdline or "Fooocus" in p_cwd:
                        proc.kill()
                        killed += 1
                        continue
                if "comfyui" in pn and "python.exe" in name.lower():
                    if (
                        "comfyui\\main.py" in cmdline.lower()
                        or "comfyui" in p_cwd.lower()
                    ):
                        proc.kill()
                        killed += 1
                        continue
                if "v2v" in pn and "python.exe" in name.lower():
                    if "v2v" in cmdline.lower() or "v2v_engine" in p_cwd.lower():
                        proc.kill()
                        killed += 1
                        continue
                if targets and any(t.lower() in name.lower() for t in targets):
                    proc.kill()
                    killed += 1
            except (psutil.AccessDenied, psutil.NoSuchProcess):
                continue

        if killed > 0:
            log.info(f"Stopped {provider_name} ({killed} processes)")
            return {
                "success": True,
                "message": f"{provider_name} detenido ({killed} procesos cerrados en Nodo).",
            }
        else:
            return {"success": False, "error": "No se encontró el proceso en el Nodo."}


def run_node(port=8888):
    server_address = ("0.0.0.0", port)
    httpd = HTTPServer(server_address, SwarmNodeHandler)
    log.info(f"Gravity Swarm Node running on port {port}...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    log.info("Swarm Node stopped.")


if __name__ == "__main__":
    run_node()
