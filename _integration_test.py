import urllib.request
import urllib.parse
import json
import time
import subprocess


def send_post(path, payload):
    url = f"http://127.0.0.1:7860{path}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("Authorization", "Bearer dummy-token")

    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            err_body = json.loads(e.read().decode("utf-8"))
        except:  # noqa: E722
            err_body = str(e)
        return e.code, err_body
    except Exception as e:
        return 0, str(e)


def run_tests():
    print("[*] Iniciando Gravity AI Server en segundo plano...")
    server_process = subprocess.Popen(
        ["python", "bridge_server.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    print("[*] Esperando 12 segundos para la inicialización completa de daemons...")
    time.sleep(12)

    results = {}

    tests = [
        {
            "name": "Tool: Search",
            "path": "/v1/tools/search",
            "payload": {"query": "python 3.11 release date"},
        },
        {"name": "Tool: Git", "path": "/v1/tools/git", "payload": {"cmd": "status"}},
        {
            "name": "Tool: Code Run",
            "path": "/v1/tools/run",
            "payload": {"code": "print('Hello World')", "lang": "python"},
        },
        {
            "name": "Tool: Scrape",
            "path": "/v1/tools/scrape",
            "payload": {"url": "https://example.com"},
        },
        {"name": "Config: RAG Toggle", "path": "/v1/rag/toggle", "payload": {}},
        {
            "name": "Config: Bounty Profile",
            "path": "/v1/bounties/profile",
            "payload": {"profile": "Test Freelancer Profile"},
        },
    ]

    for t in tests:
        print(f"[*] Testeando {t['name']} ({t['path']})...")
        status, response = send_post(t["path"], t["payload"])
        results[t["name"]] = {"status": status, "response": response}
        print(f"    -> Status: {status}")

    print("[*] Cerrando el servidor de pruebas...")
    server_process.terminate()
    try:
        server_process.wait(timeout=5)
    except:  # noqa: E722
        server_process.kill()

    print("\n\n=== REPORTE DE INTEGRACIÓN END-TO-END ===")
    all_ok = True
    for name, res in results.items():
        status = res["status"]
        if status == 200:
            print(f"[EXITO] {name} respondio 200 OK.")
        else:
            all_ok = False
            print(f"[FALLO] {name} respondio {status}. Error: {res['response']}")

    if all_ok:
        print("\n[OK] TODOS LOS SISTEMAS FUNCIONAN AL 100%. NINGÚN CRASH DETECTADO.")
    else:
        print("\n[!] SE DETECTARON FALLOS EN LA API REST.")


if __name__ == "__main__":
    run_tests()
