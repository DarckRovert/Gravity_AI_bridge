import os

pipeline_path = r"F:\Gravity_AI_bridge\core\video_pipeline.py"

with open(pipeline_path, "rb") as f:
    content = f.read().decode("utf-8", errors="replace")

# Verificar si la DEFINICION existe (no solo la referencia)
definition_marker = "STYLE_COLOR_GRADES = {"
if definition_marker in content:
    print("La DEFINICION de STYLE_COLOR_GRADES ya existe - OK")
else:
    print("La DEFINICION no existe. Inyectando...")
    
    # Buscar el marcador de insercion (despues de DEFAULT_STYLE)
    # Usando bytes para encontrar el texto real en el archivo
    marker = 'DEFAULT_STYLE = "documental"'
    idx = content.find(marker)
    
    if idx == -1:
        # Intentar encontrar DEFAULT_STYLE de otra manera
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'DEFAULT_STYLE' in line:
                print(f"Encontrado DEFAULT_STYLE en linea {i+1}: {repr(line)}")
        print("ERROR: No se pudo ubicar el marcador de insercion exacto")
    else:
        inject = """

# -- Color Grades por Estilo (cinematic auto-grading) --------------------------
STYLE_COLOR_GRADES = {
    "documental": "eq=contrast=1.05:brightness=0.02:saturation=0.9",
    "anime":      "eq=contrast=1.1:brightness=0.0:saturation=1.5",
    "epico":      "eq=contrast=1.3:brightness=-0.05:saturation=1.2:gamma=0.9,colorbalance=rs=0.05:gs=-0.02:bs=-0.05",
    "noir":       "eq=contrast=1.4:brightness=-0.1:saturation=0.0:gamma=0.85",
    "infantil":   "eq=contrast=0.95:brightness=0.05:saturation=1.4",
    "naturaleza": "eq=contrast=1.1:brightness=0.03:saturation=1.3,colorbalance=rs=-0.05:gs=0.05:bs=0.0",
    "cyberpunk":  "eq=contrast=1.3:brightness=-0.05:saturation=1.1,colorbalance=rs=-0.1:gs=-0.1:bs=0.3",
    "historico":  "eq=contrast=1.1:brightness=0.02:saturation=0.75:gamma=1.05,colorbalance=rs=0.1:gs=0.05:bs=-0.1",
    "lofi":       "eq=contrast=0.9:brightness=0.05:saturation=0.8:gamma=1.1",
    "retro80s":   "eq=contrast=1.15:brightness=0.0:saturation=1.4,colorbalance=rs=0.05:gs=-0.1:bs=0.15",
    "cinematic":  "eq=contrast=1.2:brightness=-0.03:saturation=0.95:gamma=0.95,colorbalance=rs=0.03:gs=0.0:bs=-0.05",
}
"""
        end = idx + len(marker)
        content = content[:end] + inject + content[end:]
        
        with open(pipeline_path, "w", encoding="utf-8") as f:
            f.write(content)
        print("STYLE_COLOR_GRADES DEFINICION inyectada correctamente")
        
        # Verificar
        content2 = open(pipeline_path, "rb").read().decode("utf-8", errors="replace")
        if definition_marker in content2:
            print("VERIFICACION OK: la definicion esta presente en el archivo")
        else:
            print("ERROR: la definicion no se guardó correctamente")
