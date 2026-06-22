import os
import sys
import json
import time

# Añadimos el root de Gravity_AI_bridge para poder importar
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.provider_manager import complete

DIRECTORIES = [
    r"F:\Gravity_AI_bridge\ensayos_generados",
    r"F:\Gravity_AI_bridge\ficcion_generada",
    r"F:\Gravity_AI_bridge\libros_generados",
    r"F:\gravity-news-portal\dist\books",
    r"F:\gravity-news-portal\public\books"
]

PROMPT_SISTEMA = """Eres un editor experto en estilo Cyberpunk.
Tu trabajo es revisar este texto en español (generado por una IA previa).
DEBES CORREGIR:
- Errores ortográficos (ej. "acostumado" -> "acostumbrado").
- Sintaxis o gramática que esté rota.

ESTÁ ESTRICTAMENTE PROHIBIDO:
- Cambiar nombres propios (Leviatán, Ostrom, Sabuesos, Altair-7, Lyra, Kaelen, DarckRovert, etc).
- Suavizar el tono oscuro, filosófico y violento.
- Cambiar etiquetas Markdown o HTML.

Solo devuelve el texto corregido. No añadas NINGUNA nota conversacional como "Aquí tienes el texto corregido", ni comillas adicionales. Si no hay errores, devuelve el texto exactamente igual."""

STATE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "corrector_estado.json")

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"processed": []}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)

def process_paragraph(paragraph: str) -> str:
    if not paragraph.strip() or len(paragraph) < 10:
        return paragraph
    
    # Preservar indentación original
    leading_ws = paragraph[:len(paragraph) - len(paragraph.lstrip())]
    trailing_ws = paragraph[len(paragraph.rstrip()):]
    
    messages = [
        {"role": "system", "content": PROMPT_SISTEMA},
        {"role": "user", "content": paragraph.strip()}
    ]
    
    try:
        # Forzamos el uso de la IA local (LM Studio) en lugar de dejar que ProviderManager escoja NIM (Nube)
        response = complete(messages=messages, provider="LM Studio", task="reason").strip()
        
        # Purga de bloques de código markdown alucinados
        if response.startswith("```"):
            lines = response.split("\n")
            if len(lines) >= 2 and lines[0].startswith("```") and lines[-1].startswith("```"):
                response = "\n".join(lines[1:-1]).strip()
                
        # Defensa de fallo silencioso (respuesta vacía)
        if not response.strip():
            print("\n  [!] El modelo devolvió una cadena vacía. Descartando corrección.")
            return paragraph
            
        # Defensa anti-truncamiento / sumarización
        # Si la respuesta es menos del 60% del original o más del 150%, probablemente alucinó o resumió.
        orig_len = len(paragraph.strip())
        resp_len = len(response)
        if resp_len < orig_len * 0.6 or resp_len > orig_len * 1.5:
            print(f"\n  [!] Variación de longitud sospechosa ({orig_len} vs {resp_len}). Descartando corrección.")
            return paragraph
        
        # Anti-hallucination defense: Remove conversational prefixes
        lower_resp = response.lower()
        if lower_resp.startswith("aquí") or lower_resp.startswith("texto") or lower_resp.startswith("claro") or lower_resp.startswith("este es"):
            print("\n  [!] Alucinación conversacional detectada. Descartando corrección.")
            return paragraph
            
        # Provider Manager offline defense
        if response.startswith("[ProviderManager]"):
            print(f"\n  [!] Error crítico del motor de IA: {response}")
            print("  [!] Abortando para evitar sobrescribir con mensajes de error.")
            sys.exit(1)
            
        return leading_ws + response + trailing_ws
    except Exception as e:
        print(f"\n  [!] Error procesando párrafo: {e}")
        return paragraph # Fallback to original

def run():
    state = load_state()
    print("Iniciando Corrector Semántico Cyberpunk con ProviderManager...")
    
    for d in DIRECTORIES:
        if not os.path.exists(d):
            continue
            
        for root, _, files in os.walk(d):
            for file in files:
                if not file.endswith(('.md', '.html')):
                    continue
                
                filepath = os.path.join(root, file)
                if filepath in state["processed"]:
                    continue
                    
                print(f"\nAuditando: {filepath}")
                try:
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                except Exception as e:
                    print(f"Error leyendo: {e}")
                    continue
                
                # Lógica dinámica de separación según extensión del archivo
                if file.endswith('.md'):
                    # En Markdown, los párrafos reales se separan por un doble salto de línea
                    paragraphs = content.split("\n\n")
                    separator = "\n\n"
                else:
                    # En HTML, las etiquetas como <p> suelen venir línea por línea
                    paragraphs = content.split("\n")
                    separator = "\n"
                    
                new_paragraphs = []
                
                for i, p in enumerate(paragraphs):
                    print(f"  -> Procesando párrafo {i+1}/{len(paragraphs)}", end="\r")
                    new_p = process_paragraph(p)
                    new_paragraphs.append(new_p)
                    
                print("\n  [✓] Archivo procesado.")
                
                new_content = separator.join(new_paragraphs)
                if new_content != content:
                    tmp_filepath = filepath + ".tmp"
                    with open(tmp_filepath, 'w', encoding='utf-8') as f:
                        f.write(new_content)
                    os.replace(tmp_filepath, filepath)
                
                state["processed"].append(filepath)
                save_state(state)

if __name__ == "__main__":
    # Test with just ONE file for the user to see it works
    # We will slice the directory walk to just do a fast test if needed, but for now we just run it.
    run()
