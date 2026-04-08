import os
import sys

# Ruta de origen y destino
path_en = r"E:\Turtle Wow\Interface\AddOns\pfQuest\db\enUS\quests.lua"
path_out = r"E:\Turtle Wow\Interface\AddOns\pfQuest\db\esES\quests-turtle.lua"

if not os.path.exists(path_en):
    print(f"Error: {path_en} no existe.")
    sys.exit(1)

print(f"Iniciando extracción desde {path_en}...")

with open(path_en, "r", encoding="utf-8") as f:
    lines = f.readlines()

turtle_quests = []
current_quest = None
save = False

# Procesamiento línea por línea para evitar problemas de regex en archivos grandes
for line in lines:
    if line.strip().startswith("[") and "] = {" in line:
        try:
            qid_str = line.split("[")[1].split("]")[0]
            if qid_str.isdigit() and int(qid_str) >= 40000:
                save = True
                current_quest = line
            else:
                save = False
        except:
            save = False
    elif save:
        current_quest += line
        if line.strip() == "}," or line.strip() == "}":
            turtle_quests.append(current_quest)
            save = False
            if len(turtle_quests) % 100 == 0:
                print(f"Procesadas {len(turtle_quests)} misiones...")

with open(path_out, "w", encoding="utf-8") as f:
    f.write('pfDB["quests"]["esES-turtle"] = {\n')
    f.write("".join(turtle_quests))
    f.write("\n}\n")

print(f"Extracción exitosa: {len(turtle_quests)} entradas encontradas.")
