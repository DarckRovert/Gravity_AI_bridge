import asyncio
import websockets
import json
import urllib.request
import urllib.error
import sys
import io
import random
import string

# Forzar utf-8 para consolas cp1252
if sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

async def run_gradio(prompt, performance, aspect_ratio, fooocus_url="http://127.0.0.1:7861"):
    ws_url = fooocus_url.replace("http://", "ws://").replace("https://", "wss://") + "/queue/join"
    
    try:
        with urllib.request.urlopen(f"{fooocus_url}/config", timeout=5) as r:
            config = json.loads(r.read().decode())
    except Exception as e:
        print(json.dumps({"success": False, "error": f"Error conectando a Fooocus: {e}"}))
        return

    components = config.get("components", [])
    dependencies = config.get("dependencies", [])
    
    comp_data = {}
    comp_choices = {}
    cid_map = {}
    target_labels = {
        "prompt": "Prompt", 
        "neg_prompt": "Negative Prompt", 
        "perf": "Performance", 
        "aspect": "Aspect Ratios",
        "num": "Image Number"
    }
    
    for c in components:
        cid = c.get("id")
        if cid is None: continue
        props = c.get("props", {})
        label = props.get("label", "")
        comp_data[cid] = props.get("value")
        if "choices" in props:
            comp_choices[cid] = props.get("choices")
        for key, target_label in target_labels.items():
            if label == target_label:
                cid_map[key] = cid

    get_task_fn = None
    gen_clicked_fn = None

    for i, fn in enumerate(dependencies):
        inputs = fn.get("inputs", [])
        if len(inputs) > 50:
            get_task_fn = {"index": i, "inputs": inputs}
        elif fn.get("types", {}).get("generator") is True:
            # generate_clicked yields progress
            gen_clicked_fn = {"index": i, "inputs": inputs}

    if not get_task_fn or not gen_clicked_fn:
        print(json.dumps({"success": False, "error": "generadores web no encontrados en config"}))
        return

    # Mapeo posicional del prompt real (textbox) vs Component 125 (radio)
    cid_map["prompt"] = get_task_fn["inputs"][0]
    
    args = []
    for cid in get_task_fn["inputs"]:
        val = comp_data.get(cid)
        if cid == cid_map.get("prompt"):
            val = prompt
        elif cid == cid_map.get("neg_prompt"):
            val = "low quality, bad anatomy, text, watermark, deformed"
        elif cid == cid_map.get("perf"):
            val = performance
        elif cid == cid_map.get("aspect"):
            base_aspect = aspect_ratio.replace("*", "×")
            val = base_aspect
            if cid in comp_choices:
                for choice in comp_choices[cid]:
                    choice_val = choice[1] if isinstance(choice, list) and len(choice) > 1 else choice
                    if isinstance(choice_val, str) and choice_val.startswith(base_aspect):
                        val = choice_val
                        break
        elif cid == cid_map.get("num"):
            val = 1
        args.append(val)

    expected_len = len(get_task_fn["inputs"])
    if len(args) > expected_len:
        args = args[:expected_len]
    elif len(args) < expected_len:
        args.extend([None] * (expected_len - len(args)))

    session_hash = "gravity_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=10))
    print(f"[NativeTrigger] WS State init. (session: {session_hash}, params: {len(args)})", file=sys.stderr)

    try:
        # FASE 1: Setear variables en memoria
        async with websockets.connect(ws_url, max_size=None, ping_interval=None) as ws:
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                
                if data["msg"] == "send_hash":
                    await ws.send(json.dumps({"fn_index": get_task_fn["index"], "session_hash": session_hash}))
                elif data["msg"] == "send_data":
                    await ws.send(json.dumps({"fn_index": get_task_fn["index"], "session_hash": session_hash, "data": args}))
                elif data["msg"] == "process_completed":
                    if not data.get("success", True):
                        print(json.dumps({"success": False, "error": data.get("output", {}).get("error", "Init fallback")}))
                        return
                    break

        print(f"[NativeTrigger] WS Generando imagen (fn_index: {gen_clicked_fn['index']})", file=sys.stderr)
        # FASE 2: Iniciar Generator Thread
        async with websockets.connect(ws_url, max_size=None, ping_interval=None) as ws:
            while True:
                msg = await ws.recv()
                data = json.loads(msg)
                
                if data["msg"] == "send_hash":
                    await ws.send(json.dumps({"fn_index": gen_clicked_fn["index"], "session_hash": session_hash}))
                elif data["msg"] == "send_data":
                    # Pasa argumentos requeridos por generate_clicked (None para state args)
                    gen_args = [None for _ in gen_clicked_fn["inputs"]]
                    await ws.send(json.dumps({"fn_index": gen_clicked_fn["index"], "session_hash": session_hash, "data": gen_args}))
                elif data["msg"] == "process_generating":
                    # Logs silenciosos o progress
                    pass
                elif data["msg"] == "process_completed":
                    # Output: {'data': [html, preview, finished_images, gallery]}
                    out_data = data.get("output", {}).get("data", [])
                    # gallery o finished_images puede tener metadata
                    gallery = []
                    for i in (3, 2):  # índices comunes para gallery
                        if len(out_data) > i and isinstance(out_data[i], list):
                            gallery = out_data[i]
                            break
                    
                    real_images = []
                    for im in gallery:
                        if isinstance(im, dict) and "name" in im:
                            real_images.append(im["name"])
                        elif isinstance(im, list) and len(im) > 0 and isinstance(im[0], dict) and "name" in im[0]: # Gradio < 3.42 fallback
                             real_images.append(im[0]["name"])
                    
                    print(json.dumps({"success": True, "images": real_images, "data": data.get("output", {})}))
                    break
                    
    except Exception as e:
        print(json.dumps({"success": False, "error": f"WS Exception: {str(e)}"}))

def main():
    if len(sys.argv) < 4:
        print(json.dumps({"success": False, "error": "Faltan argumentos (prompt, performance, aspect_ratio)"}))
        sys.exit(1)
    
    prompt = sys.argv[1]
    performance = sys.argv[2]
    aspect_ratio = sys.argv[3]
    
    asyncio.run(run_gradio(prompt, performance, aspect_ratio))

if __name__ == "__main__":
    main()
