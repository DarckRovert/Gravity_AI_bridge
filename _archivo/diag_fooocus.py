import urllib.request
import json
import sys

def diag():
    fooocus_url = "http://127.0.0.1:7861"
    try:
        with urllib.request.urlopen(f"{fooocus_url}/config", timeout=5) as r:
            config = json.loads(r.read().decode())
        
        dependencies = config.get("dependencies", [])
        gen_fn = None
        for fn in dependencies:
            if len(fn.get("inputs", [])) > 100:
                gen_fn = fn
                break
        
        if gen_fn:
            inputs = gen_fn.get("inputs", [])
            print(f"DIAG: Servidor requiere {len(inputs)} argumentos para el fn_index detectado.")
        else:
            print("DIAG: No se encontró la función de generación (>100 inputs).")
            
    except Exception as e:
        print(f"DIAG ERROR: {e}")

if __name__ == "__main__":
    diag()
