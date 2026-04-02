import sys
import json
import urllib.request
import urllib.error

def query_ollama(prompt, model="deepseek-r1:8b"):
    url = 'http://localhost:11434/api/generate'
    
    data = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    
    req = urllib.request.Request(
        url, 
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'}
    )

    try:
        response = urllib.request.urlopen(req)
        result = json.loads(response.read().decode('utf-8'))
        return result.get('response', '')
    except urllib.error.URLError as e:
        return f"Error conectando a Ollama: {e}"

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python ask_deepseek.py \"Tu pregunta o tarea aquí\"")
        sys.exit(1)
        
    prompt = sys.argv[1]
    # Comprobar si se proporcionó todo en un solo arg o varios, en caso de comillas imperfectas
    if len(sys.argv) > 2:
        prompt = " ".join(sys.argv[1:])
        
    print("--- Consultando a deepseek-r1:8b ---")
    respuesta = query_ollama(prompt)
    print("\n--- Respuesta de Deepseek-R1 ---")
    print(respuesta)
    print("\n--------------------------------")
