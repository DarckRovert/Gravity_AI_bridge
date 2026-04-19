import os
import re

root = r"F:\Gravity_AI_bridge"
pattern = re.compile(r'\b(v|V)[789](\.[0-9]+)+\b')

for root_dir, dirs, files in os.walk(root):
    if "_integrations" in dirs: dirs.remove("_integrations")
    if "node_modules" in dirs: dirs.remove("node_modules")
    if ".git" in dirs: dirs.remove(".git")
    if "__pycache__" in dirs: dirs.remove("__pycache__")
    
    for file in files:
        if file.endswith((".py", ".html", ".bat", ".md", ".json", ".yaml", ".txt")):
            path = os.path.join(root_dir, file)
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f, 1):
                        if pattern.search(line):
                            print(f"{path}:{i} -> {line.strip()}")
            except Exception:
                pass
