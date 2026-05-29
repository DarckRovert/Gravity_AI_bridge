import os

base_dir = r"F:\Gravity_AI_bridge\_integrations\FabricaWeb"
md_files = [f for f in os.listdir(base_dir) if f.endswith(".md")]

replacements = {
    "pastelito-next": "gravity-web-core",
    "Pastelito AI": "Gravity Web Core",
    "PastelitoEngine": "CoreNLPEngine",
    "pastelitoEngine": "coreNLP",
    "Pastelito": "Asistente",
    "Dulces Momentos": "Plantilla Maestra"
}

for md in md_files:
    file_path = os.path.join(base_dir, md)
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
    
    original_content = content
    for old, new in replacements.items():
        content = content.replace(old, new)
        
    if content != original_content:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Updated {md}")
