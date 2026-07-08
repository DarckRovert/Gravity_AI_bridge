import os
import sys
import json

# Añadimos el root de Gravity_AI_bridge para poder importar
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.provider_manager import complete

DIRECTORIES = [
    r"F:\Gravity_AI_bridge\ensayos_generados",
    r"F:\Gravity_AI_bridge\ficcion_generada",
    r"F:\Gravity_AI_bridge\libros_generados",
    r"F:\gravity-news-portal\dist\books",
    r"F:\gravity-news-portal\public\books",
]

PROMPT_SISTEMA = """Eres un corrector ortográfico y gramatical implacable.
Tu ÚNICO trabajo es revisar este texto en español (generado por una IA previa) y arreglar fallas técnicas.

DEBES CORREGIR:
- Errores ortográficos (ej. "acostumado" -> "acostumbrado").
- Sintaxis o gramática que esté visiblemente rota.
- Puntuación básica si es estrictamente necesario.

ESTÁ ESTRICTAMENTE PROHIBIDO:
- Reescribir las frases, parafrasear o cambiar el estilo del autor.
- Reemplazar palabras válidas por sinónimos "mejores". Solo corrige lo que está mal escrito.
- Cambiar nombres propios (Leviatán, Ostrom, Sabuesos, Altair-7, Lyra, Kaelen, DarckRovert, etc).
- Suavizar el tono oscuro, filosófico y violento.
- Alterar cualquier etiqueta Markdown o código HTML.

Solo devuelve el texto corregido. No añadas NINGUNA nota conversacional como "Aquí tienes el texto corregido", ni comillas adicionales. Si no encuentras faltas de ortografía, devuelve el texto EXACTAMENTE IGUAL sin tocar una sola letra."""

_app_data = os.path.join(
    os.environ.get("LOCALAPPDATA", os.path.expanduser("~\\AppData\\Local")), 
    "Gravity", 
    "Databases"
)
os.makedirs(_app_data, exist_ok=True)
STATE_FILE = os.path.join(_app_data, "corrector_estado.json")


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"processed": []}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=4)


def process_paragraph(paragraph: str, max_retries: int = 2) -> str:
    if not paragraph.strip() or len(paragraph) < 10:
        return paragraph

    # Preservar indentación original
    leading_ws = paragraph[: len(paragraph) - len(paragraph.lstrip())]
    trailing_ws = paragraph[len(paragraph.rstrip()) :]

    messages = [
        {"role": "system", "content": PROMPT_SISTEMA},
        {"role": "user", "content": paragraph.strip()},
    ]

    for attempt in range(max_retries + 1):
        try:
            # get_best will automatically pick Ollama or API
            response = complete(messages=messages, task="reason").strip()

            # Purga de bloques de código markdown alucinados
            if response.startswith("```"):
                lines = response.split("\n")
                if (
                    len(lines) >= 2
                    and lines[0].startswith("```")
                    and lines[-1].startswith("```")
                ):
                    response = "\n".join(lines[1:-1]).strip()

            # Defensa de fallo silencioso (respuesta vacía)
            if not response.strip():
                if attempt < max_retries:
                    print(
                        f"\n  [!] Respuesta vacía (intento {attempt+1}). Reintentando..."
                    )
                    continue
                print(
                    "\n  [!] El modelo devolvió una cadena vacía reiteradamente. Descartando corrección."
                )
                return paragraph

            # Defensa anti-truncamiento / sumarización
            orig_len = len(paragraph.strip())
            resp_len = len(response)
            if resp_len < orig_len * 0.6 or resp_len > orig_len * 1.5:
                if attempt < max_retries:
                    print(
                        f"\n  [!] Longitud sospechosa ({orig_len} vs {resp_len}) en intento {attempt+1}. Reintentando..."
                    )
                    continue
                print(
                    "\n  [!] Variación de longitud sospechosa permanente. Descartando corrección."
                )
                return paragraph

            # Anti-hallucination defense: Remove conversational prefixes
            lower_resp = response.lower()
            if (
                lower_resp.startswith("aquí")
                or lower_resp.startswith("texto")
                or lower_resp.startswith("claro")
                or lower_resp.startswith("este es")
            ):
                if attempt < max_retries:
                    print(
                        f"\n  [!] Alucinación conversacional (intento {attempt+1}). Reintentando..."
                    )
                    continue
                print(
                    "\n  [!] Alucinación conversacional permanente. Descartando corrección."
                )
                return paragraph

            # Provider Manager offline defense
            if response.startswith("[ProviderManager]"):
                print(f"\n  [!] Error crítico del motor de IA: {response}")
                print("  [!] Abortando para evitar sobrescribir con mensajes de error.")
                sys.exit(1)

            return leading_ws + response + trailing_ws

        except Exception as e:
            print(f"\n  [!] Error procesando párrafo: {e}")
            if attempt < max_retries:
                continue

    return paragraph  # Fallback to original si todos los reintentos fallan


def run():
    state = load_state()
    print("Iniciando Corrector Semántico Cyberpunk con ProviderManager...")

    for d in DIRECTORIES:
        if not os.path.exists(d):
            continue

        for root, _, files in os.walk(d):
            for file in files:
                if not file.endswith((".md", ".html")):
                    continue

                filepath = os.path.join(root, file)
                if filepath in state["processed"]:
                    continue

                print(f"\nAuditando: {filepath}")
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        content = f.read()
                except Exception as e:
                    print(f"Error leyendo: {e}")
                    continue

                # Lógica dinámica de separación según extensión del archivo
                if file.endswith(".md"):
                    # En Markdown, los párrafos reales se separan por un doble salto de línea
                    paragraphs = content.split("\n\n")
                    separator = "\n\n"
                else:
                    # En HTML, las etiquetas como <p> suelen venir línea por línea
                    paragraphs = content.split("\n")
                    separator = "\n"

                import concurrent.futures

                new_paragraphs = [None] * len(paragraphs)

                with concurrent.futures.ThreadPoolExecutor(max_workers=15) as executor:
                    future_to_index = {
                        executor.submit(process_paragraph, p): i
                        for i, p in enumerate(paragraphs)
                    }
                    completed = 0
                    for future in concurrent.futures.as_completed(future_to_index):
                        idx = future_to_index[future]
                        new_paragraphs[idx] = future.result()
                        completed += 1
                        print(
                            f"  -> Procesando párrafo {completed}/{len(paragraphs)} (Turbo)",
                            end="\r",
                        )

                print("\n  [✓] Archivo procesado.")

                new_content = separator.join(new_paragraphs)
                if new_content != content:
                    tmp_filepath = filepath + ".tmp"
                    with open(tmp_filepath, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    os.replace(tmp_filepath, filepath)

                state["processed"].append(filepath)
                save_state(state)


if __name__ == "__main__":
    run()

    # ── Pipeline de Automatización Final ──
    print("\n[+] Corrección finalizada. Iniciando limpieza de impurezas...")
    import subprocess

    try:
        script_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "limpiador_textos.py"
        )
        subprocess.run([sys.executable, script_path], check=True)
    except Exception as e:
        print(f"  [!] Error al ejecutar el limpiador: {e}")

    print("\n[+] Sincronizando libros con el Portal Web...")
    import shutil

    source_dirs = [
        r"F:\Gravity_AI_bridge\ensayos_generados",
        r"F:\Gravity_AI_bridge\ficcion_generada",
        r"F:\Gravity_AI_bridge\libros_generados",
    ]
    target_base = r"F:\gravity-news-portal\dist\books"
    os.makedirs(
        target_base, exist_ok=True
    )  # Aseguramos que la carpeta exista aunque el usuario la haya borrado por completo

    for src in source_dirs:
        if os.path.exists(src):
            basename = os.path.basename(src)
            dst = os.path.join(target_base, basename)
            try:
                shutil.copytree(src, dst, dirs_exist_ok=True)
                print(f"  [✓] Transferido: {basename}")
            except Exception as e:
                print(f"  [!] Error transfiriendo {basename}: {e}")

    print("\n[★] Pipeline completado. Libros publicados en el servidor web.")
