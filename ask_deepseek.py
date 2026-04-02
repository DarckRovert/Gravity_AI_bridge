import sys, json, os, urllib.request

# Configuración
H_FILE, K_FILE = '_history.json', '_knowledge.json'
URL, MODEL = 'http://localhost:11434/api/chat', 'deepseek-r1:8b'
S_PROMPT = "Eres el Auditor Senior de Gravity AI. Audita código de forma profesional.\nREGLAS:\n{rules}"

def load(f, d): return json.load(open(f, 'r', encoding='utf-8')) if os.path.exists(f) else d
def save(f, d): json.dump(d, open(f, 'w', encoding='utf-8'), ensure_ascii=False, indent=4)

def query(msgs):
    data = json.dumps({'model': MODEL, 'messages': msgs, 'stream': False}).encode()
    req = urllib.request.Request(URL, data=data, headers={'Content-Type': 'application/json'})
    return json.loads(urllib.request.urlopen(req).read().decode())['message']['content']

def chat():
    print("GRAVITY AI BRIDGE V2 - AUDITOR SENIOR\nComandos: /leer, !aprende, !limpiar, salir\n")
    hist = []
    while True:
        try:
            inp = input(">> ").strip()
            if not inp or inp.lower() in ['salir', 'exit']: break
            if inp.startswith('!aprende '):
                r = load(K_FILE, []); r.append(inp[9:]); save(K_FILE, r); print("[+] Aprendido."); continue
            if inp.startswith('!limpiar'): hist = []; print("[!] Limpio."); continue
            if inp.startswith('/leer '):
                p = inp[6:].strip()
                if os.path.exists(p):
                    inp = f"CONTENIDO DE {p}:\n\n{open(p, 'r', encoding='utf-8').read()}"
                    print(f"[+] {p} cargado.");
                else: print("[!] No existe."); continue
            
            rules = "\n".join([f"- {r}" for r in load(K_FILE, [])])
            msgs = [{'role': 'system', 'content': S_PROMPT.format(rules=rules)}] + hist + [{'role': 'user', 'content': inp}]
            print("--- Pensando ---")
            ans = query(msgs)
            print(f"\nAUDITOR:\n{ans}\n")
            hist = (hist + [{'role': 'user', 'content': inp}, {'role': 'assistant', 'content': ans}])[-10:]
            save(H_FILE, hist)
        except Exception as e: print(f"Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1: print(query([{'role': 'user', 'content': ' '.join(sys.argv[1:])}]))
    else: chat()
