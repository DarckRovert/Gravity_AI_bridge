import urllib.request
import json
import time
import socket
from concurrent.futures import ThreadPoolExecutor

class ProviderResult:
    def __init__(self, name, url, protocol):
        self.name = name
        self.url = url
        self.protocol = protocol
        self.is_healthy = False
        self.models = []
        self.active_model = None
        self.response_ms = 0
        
    @property
    def model_count(self):
        return len(self.models)

class ProviderScanner:
    KNOWN_PROVIDERS = [
        {"name": "Ollama", "port": 11434, "protocol": "ollama"},
        {"name": "LM Studio", "port": 1234, "protocol": "openai"},
        {"name": "Lemonade", "port": 8000, "protocol": "openai"},
        {"name": "Jan AI", "port": 1337, "protocol": "openai"}
    ]
    
    @staticmethod
    def _safe_request(url, timeout=1.5):
        try:
            # Forzamos timeout a nivel socket para Windows por si urlopen bloquea
            socket.setdefaulttimeout(timeout)
            req = urllib.request.Request(url, headers={"User-Agent": "GravityAI/4.0"})
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return json.loads(response.read().decode('utf-8'))
        except Exception:
            return None

    @staticmethod
    def scan_provider(prov_info):
        url_base = f"http://localhost:{prov_info['port']}"
        result = ProviderResult(prov_info["name"], url_base, prov_info["protocol"])
        
        start_time = time.time()
        
        if prov_info["protocol"] == "ollama":
            # 1. Obtener modelos
            tags_data = ProviderScanner._safe_request(f"{url_base}/api/tags")
            if tags_data and "models" in tags_data:
                result.is_healthy = True
                result.models = [{"name": m["name"], "size": m.get("size", 0)} for m in tags_data["models"]]
                
                # 2. Ver si alguno está cargado en GPU activo
                ps_data = ProviderScanner._safe_request(f"{url_base}/api/ps")
                if ps_data and "models" in ps_data and len(ps_data["models"]) > 0:
                    result.active_model = ps_data["models"][0]["name"]
                    
        elif prov_info["protocol"] == "openai":
            # Solo un request a /v1/models
            models_data = ProviderScanner._safe_request(f"{url_base}/v1/models")
            if models_data and "data" in models_data:
                result.is_healthy = True
                result.models = [{"name": m.get("id"), "size": 0} for m in models_data.get("data", [])]
                
                # Intentar deducir si está activo en base a particularidades de APIs (LM Studio)
                # LM Studio muchas veces tiene campos extra si el modelo está en memoria, pero para simplificar,
                # Asumiremos como activo el primero si es LLM cargado, pero no hay garantía exacta por API V1. 
                # (Solo Ollama usa /api/ps). Así que el scanner de GPU de LM Studio a veces depende de config manual.
                # Sin embargo, si LM Studio responde modelos, es porque está levantando la capa server.
                # Muchos proxy (como LM Studio) suelen devolver solo los modelos ACTUALMENTE cargados en /v1/models.
                # Vamos a tomar heurísticamente el primero como activo si existe, ya que LM Studio solo levanta lo que está en memoria.
                if len(result.models) == 1:
                    result.active_model = result.models[0]["name"]
                elif len(result.models) > 1 and prov_info["name"] == "LM Studio":
                    result.active_model = result.models[0]["name"] # LM Studio suele listar el principal que tiene cargado arriba de todo
                    
        end_time = time.time()
        result.response_ms = int((end_time - start_time) * 1000)
        
        return result

    @staticmethod
    def scan_all():
        results = []
        with ThreadPoolExecutor(max_workers=len(ProviderScanner.KNOWN_PROVIDERS)) as executor:
            scans = list(executor.map(ProviderScanner.scan_provider, ProviderScanner.KNOWN_PROVIDERS))
            for res in scans:
                # Filtrar solo válidos o mantenerlos para el dash? Los devolvemos todos, el dashboard decide.
                results.append(res)
        return results

    @staticmethod
    def get_parameter_score(model_name):
        """Asigna puntaje rudimentario basado en parámetros (ej: 32b > 14b > 8b)"""
        if not model_name:
            return 0
        name = model_name.lower()
        if "70b" in name or "72b" in name: return 70
        if "32b" in name or "33b" in name: return 32
        if "14b" in name or "13b" in name: return 14
        if "8b" in name or "7b" in name: return 8
        if "3b" in name or "1b" in name: return 3
        return 1

    @staticmethod
    def auto_select_best(results):
        """Devuelve una tupla (mejor_resultado, modelo_elegido_como_str)"""
        healthy = [r for r in results if r.is_healthy and r.models]
        if not healthy:
            return None, None
            
        # 1. Priorizar si alguno tiene ya un active_model cargado en GPU
        loaded = [r for r in healthy if r.active_model]
        if loaded:
            # De los cargados, elegir el de mayor peso
            loaded.sort(key=lambda x: ProviderScanner.get_parameter_score(x.active_model), reverse=True)
            return loaded[0], loaded[0].active_model
            
        # 2. Si nada está en GPU (Ollama dormido), elegir el de mayor peso de cualquier proveedor
        best_prov = None
        best_mod = None
        best_score = -1
        
        for r in healthy:
            # Ordenar los modelos de este proveedor
            r.models.sort(key=lambda m: ProviderScanner.get_parameter_score(m["name"]), reverse=True)
            top_model = r.models[0]["name"]
            score = ProviderScanner.get_parameter_score(top_model)
            if score > best_score:
                best_score = score
                best_prov = r
                best_mod = top_model
                
        # 3. Y si todo es ambiguo, solo tomamos el más rápido (menor latencia) garantizando algo
        if not best_prov:
            healthy.sort(key=lambda x: x.response_ms)
            return healthy[0], healthy[0].models[0]["name"]
            
        return best_prov, best_mod

if __name__ == "__main__":
    # Test block
    print("Iniciando escaneo paralelo...")
    scans = ProviderScanner.scan_all()
    for s in scans:
        print(f"[{'X' if s.is_healthy else ' '}] {s.name:<12} | URL: {s.url} | {s.response_ms}ms")
        for m in s.models:
            active = "*" if m["name"] == s.active_model else " "
            print(f"    {active} {m['name']}")
    
    best_prov, best_mod = ProviderScanner.auto_select_best(scans)
    if best_prov:
         print(f"\nMEJOR: {best_prov.name} -> {best_mod}")
