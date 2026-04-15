import urllib.request
import json
import sys
import io

# Forzar utf-8 para que las librerías Gradio 0.5 de Fooocus no colapsen en consolas cp1252
if sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

from gradio_client import Client

def main():
    if len(sys.argv) < 4:
        print(json.dumps({"success": False, "error": "Faltan argumentos (prompt, performance, aspect_ratio)"}))
        sys.exit(1)
        
    prompt = sys.argv[1]
    performance = sys.argv[2]
    aspect_ratio = sys.argv[3]
    
    fooocus_url = "http://127.0.0.1:7861"
    
    try:
        # 1. Obtener Componentes Dinámicos (Resuelve el error "needed: 153, got: X")
        with urllib.request.urlopen(f"{fooocus_url}/config", timeout=5) as r:
            config = json.loads(r.read().decode())
        
        components = config.get("components", [])
        dependencies = config.get("dependencies", [])
        
        cid_map = {}
        target_labels = {
            "prompt": "Prompt", 
            "neg_prompt": "Negative Prompt", 
            "perf": "Performance", 
            "aspect": "Aspect Ratios",
            "num": "Image Number"
        }
        
        comp_data = {}
        for c in components:
            cid = c.get("id")
            if cid is None: continue
            
            props = c.get("props", {})
            label = props.get("label", "")
            value = props.get("value")
            comp_data[cid] = value
            
            for key, target_label in target_labels.items():
                if label == target_label:
                    cid_map[key] = cid

        # 2. Localizar función de Generación
        gen_fn = None
        for fn in dependencies:
            if len(fn.get("inputs", [])) > 100:
                gen_fn = fn
                break
                
        if not gen_fn:
            print(json.dumps({"success": False, "error": "generador web no encontrado"}))
            return
            
        fn_index = dependencies.index(gen_fn)
        input_ids = gen_fn.get("inputs", [])
        
        args = []
        for cid in input_ids:
            val = comp_data.get(cid)
            if cid == cid_map.get("prompt"):
                val = prompt
            elif cid == cid_map.get("neg_prompt"):
                val = "low quality, bad anatomy, text, watermark, deformed"
            elif cid == cid_map.get("perf"):
                val = performance
            elif cid == cid_map.get("aspect"):
                val = aspect_ratio
            elif cid == cid_map.get("num"):
                val = 1
            args.append(val)

        # 3. Disparo con cliente de Gradio de la misma JVM/Python (Bypass Queues y WS)
        client = Client(fooocus_url)
        job = client.submit(*args, fn_index=fn_index)
        
        # Debemos esperar a que empiece a procesar para no desconectar el socket, 
        # Si cerramos Inmediatamente, Gradio detecta desconexión y cancela la generación.
        # Imprimimos de inmediato para el stdout del Bridge, pero el script se queda vivo esperando.
        print(json.dumps({"success": True}))
        sys.stdout.flush()
        
        # Bloquea hasta que la generación acabe (mantiene vivo el socket)
        try:
            res_val = job.result()
            print(f"JOB RESULT: {res_val}", file=sys.stderr)
        except Exception as err:
            print(f"JOB ERROR: {err}", file=sys.stderr)
            
    except Exception as e:
        print(json.dumps({"success": False, "error": str(e)}))

if __name__ == "__main__":
    main()
