import os
import re

directories = [
    r"F:\Gravity_AI_bridge\ensayos_generados",
    r"F:\Gravity_AI_bridge\ficcion_generada",
    r"F:\Gravity_AI_bridge\libros_generados",
    r"F:\gravity-news-portal\public\books"
]

def process_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return

    original_content = content

    # 1. Removals (regex)
    
    # Remove ***[COMIENZO DEL CAPÍTULO X]*** and HTML variants
    content = re.sub(r'(<p>)?\s*(?:<[^>]+>)*\**\[COMIENZO DEL CAPÍTULO \d+\]\**(?:</[^>]+>)*\s*(</p>)?\n*', '', content, flags=re.IGNORECASE)
    
    # Remove ***[FIN DEL CAPÍTULO X]***
    content = re.sub(r'(<p>)?\s*(?:<[^>]+>)*\**\[FIN DEL CAPÍTULO \d+\]\**(?:</[^>]+>)*\s*(</p>)?\n*', '', content, flags=re.IGNORECASE)
    
    # Remove *(Fin del Capítulo X)*
    content = re.sub(r'(<p>)?\s*(?:<[^>]+>)*\**\(Fin del Capítulo \d+\)\**(?:</[^>]+>)*\s*(</p>)?\n*', '', content, flags=re.IGNORECASE)
    
    # Remove [ADVERTENCIA: EL TONO...]
    content = re.sub(r'(<p>)?\s*(?:<[^>]+>)*\**\[ADVERTENCIA:[^\]]+\]\**(?:</[^>]+>)*\s*(</p>)?\n*', '', content, flags=re.IGNORECASE)
    
    # Remove [AMBIENTE CINEMÁTICO SUGERIDO:...]
    content = re.sub(r'(<p>)?\s*(?:<[^>]+>)*\**\[AMBIENTE CINEMÁTICO SUGERIDO:[^\]]+\]\**(?:</[^>]+>)*\s*(</p>)?\n*', '', content, flags=re.IGNORECASE)
    
    # 2. Fix explicit typos
    content = content.replace("acostumado", "acostumbrado")
    content = content.replace("Acostumado", "Acostumbrado")
    
    # 3. Fix narrative placeholders (Prompt bleeding inside the text)
    content = content.replace("[su nombre]", "Lyra")
    content = content.replace("[Su nombre]", "Lyra")
    content = content.replace("[Su Nombre]", "Lyra")
    content = content.replace("[Su Nombre/IA Supervisor]", "DarckRovert")
    content = content.replace("[Hoy]", "2142")
    content = content.replace("[Su Nombre/Autor]", "DarckRovert")
    
    # Remove extra empty lines left behind by the removed blocks (more than 2 consecutive newlines)
    content = re.sub(r'\n{3,}', '\n\n', content)

    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Modificado: {filepath}")

if __name__ == "__main__":
    print("Iniciando limpieza de artefactos...")
    for d in directories:
        if os.path.exists(d):
            print(f"Explorando directorio: {d}")
            for root, dirs, files in os.walk(d):
                for file in files:
                    if file.endswith(('.md', '.html', '.json')):
                        process_file(os.path.join(root, file))
    print("Limpieza finalizada.")
