import json
import urllib.parse
from core.mcp_adapter import active_adapters


def handle_mcp_status(handler):
    try:
        servers = []
        for name, adapter in active_adapters.items():
            is_connected = (
                adapter.process is not None and adapter.process.poll() is None
            )
            servers.append(
                {
                    "name": name,
                    "connected": is_connected,
                    "tools": adapter.list_tools() if is_connected else [],
                    "resources": adapter.list_resources() if is_connected else [],
                }
            )

        body = json.dumps(
            {"mcp_servers": servers, "count": len(servers)}, indent=2
        ).encode("utf-8")
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500)
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())


def handle_mcp_resource(handler):
    try:
        params = dict(urllib.parse.parse_qsl(urllib.parse.urlparse(handler.path).query))
        server = params.get("server")
        uri = params.get("uri")

        if not server or not uri or server not in active_adapters:
            raise ValueError("Servidor o URI no válido")

        adapter = active_adapters[server]
        data = adapter.read_resource(uri)

        body = json.dumps(data, indent=2).encode("utf-8")
        handler.send_response(200)
        handler.send_header("Content-Type", "application/json")
        handler._send_cors()
        handler.end_headers()
        handler.wfile.write(body)
    except Exception as e:
        handler.send_response(500)
        handler.end_headers()
        handler.wfile.write(json.dumps({"error": str(e)}).encode())
