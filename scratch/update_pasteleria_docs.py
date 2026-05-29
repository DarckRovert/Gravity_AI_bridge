import os

base_dir = r"F:\PROYECTO PASTELERIA\pastelito-next"
md_files = [f for f in os.listdir(base_dir) if f.endswith(".md")]

replacements = {
    "Dulces Momentos": "Antojitos Express",
    "Pastelito AI": "Antojín AI",
    "pastelito-next": "antojitos-express-app"
}

for md in md_files:
    file_path = os.path.join(base_dir, md)
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    original_content = content
    for old, new in replacements.items():
        content = content.replace(old, new)
        
    # Append Web Worker note if it's the ARCHITECTURE or README
    if md == "ARCHITECTURE.md" and "nlp.worker.ts" not in content:
        content += "\n\n## 🚀 Optimización de Rendimiento\nSe ha implementado un Web Worker (`nlp.worker.ts`) para procesar el NLP (Natural Language Processing) en paralelo, manteniendo la interfaz de usuario a 60 FPS sin bloqueos en el hilo principal."
        
    if content != original_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated {md}")

# Create root README.md
root_readme_path = r"F:\PROYECTO PASTELERIA\README.md"
with open(root_readme_path, "w", encoding="utf-8") as f:
    f.write("# 🍰 Antojitos Express Web\n\nRepositorio oficial para la página web y sistema de IA autónomo (Antojín) de la tienda Antojitos Express.\n\n## Estructura\n- `pastelito-next/`: Contiene todo el código fuente de Next.js, Web Workers y Firebase.\n- `recursos graficos/`: Arte y material publicitario de la tienda.")

print("Root README created.")
