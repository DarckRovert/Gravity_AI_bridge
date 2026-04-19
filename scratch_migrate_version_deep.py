import os

def replace_in_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        modified = False
        replacements = ['V10.1', 'V10.1', 'V10.1', 'V10.1', 'V10.1', 'V10.1', 'V10.1']
        for r in replacements:
            if r in content:
                content = content.replace(r, "V10.1")
                modified = True
            lr = r.lower()
            if lr in content:
                content = content.replace(lr, "v10.1")
                modified = True
                
        if modified:
            with open(path, 'w', encoding='utf-8', newline='') as f:
                f.write(content)
            print(f"Updated: {path}")
    except Exception as e:
        print(f"Error {path}: {e}")

root = r"F:\Gravity_AI_bridge"
for root_dir, dirs, files in os.walk(root):
    if "_integrations" in dirs: dirs.remove("_integrations")
    if "node_modules" in dirs: dirs.remove("node_modules")
    if ".git" in dirs: dirs.remove(".git")
    if "__pycache__" in dirs: dirs.remove("__pycache__")
    
    for file in files:
        if file.endswith((".py", ".html", ".bat", ".md", ".json", ".yaml", ".txt")):
            replace_in_file(os.path.join(root_dir, file))
