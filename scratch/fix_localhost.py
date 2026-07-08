import os
import re

COMPONENTS_DIR = r"f:\Gravity_AI_bridge\frontend\src\components"
CONFIG_FILE = r"f:\Gravity_AI_bridge\frontend\src\config.ts"

def update_config():
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        content = f.read()
    
    new_config = """export const BRIDGE_PORT = 7860;
export const BRIDGE_BASE = typeof window !== 'undefined' 
  ? `${window.location.protocol}//${window.location.hostname}:${BRIDGE_PORT}`
  : `http://localhost:${BRIDGE_PORT}`;
"""
    # Just overwrite it entirely to be clean
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        f.write(new_config)

def process_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content
    
    # 1. Replace "http://localhost:7860/..." with `${BRIDGE_BASE}/...`
    # Replace single or double quoted strings
    content = re.sub(r'["\']http://(?:localhost|127\.0\.0\.1):7860(/[^"\']*)["\']', r'`${BRIDGE_BASE}\1`', content)
    
    # 2. Replace inside backticks: `http://localhost:7860/url` -> `${BRIDGE_BASE}/url`
    content = re.sub(r'http://(?:localhost|127\.0\.0\.1):7860', r'${BRIDGE_BASE}', content)
    
    if content != original:
        # Check if import is needed
        if "BRIDGE_BASE" in content and "import { BRIDGE_BASE }" not in content:
            # Add import after other imports
            import_statement = "import { BRIDGE_BASE } from '../config';\n"
            
            # Find the last import
            imports = list(re.finditer(r'^import .*?;?\n', content, flags=re.MULTILINE))
            if imports:
                last_import_end = imports[-1].end()
                content = content[:last_import_end] + import_statement + content[last_import_end:]
            else:
                content = import_statement + "\n" + content
                
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Fixed {os.path.basename(filepath)}")

def main():
    update_config()
    print("Updated config.ts")
    
    for filename in os.listdir(COMPONENTS_DIR):
        if filename.endswith(".tsx") or filename.endswith(".ts"):
            filepath = os.path.join(COMPONENTS_DIR, filename)
            process_file(filepath)

if __name__ == "__main__":
    main()
