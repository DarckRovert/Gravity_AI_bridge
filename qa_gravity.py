import urllib.request
import time

endpoints = [
    "/health",
    "/v1/status",
    "/v1/hardware/stats",
]

base_url = "http://127.0.0.1:7860"

def run_tests():
    print("=== Iniciando QA de Gravity API ===")
    time.sleep(10) # Dar tiempo a que el servidor arranque y cargue modulos

    for ep in endpoints:
        url = base_url + ep
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as response:
                status = response.status
                data = response.read().decode('utf-8')
                print(f"[OK] {ep} -> Status: {status}")
                if ep == "/health" or ep == "/v1/hardware/stats":
                    print(f"Response: {data[:200]}...")
        except Exception as e:
            print(f"[ERROR] Falló {ep}: {e}")

if __name__ == "__main__":
    run_tests()
