import os

ignore_dirs = {'.git', 'venv', 'node_modules', '.agents', '.gemini', 'env', '.pytest_cache'}

def refactor_dir(root_dir):
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # filter directories in-place
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs]
        for f in filenames:
            if f.endswith('.py'):
                filepath = os.path.join(dirpath, f)
                try:
                    with open(filepath, 'r', encoding='utf-8') as file:
                        content = file.read()
                    if 'hashlib.sha256(' in content or '_hl.sha256(' in content:
                        new_content = content.replace("hashlib.sha256(", "hashlib.sha256(").replace("_hl.sha256(", "_hl.sha256(")
                        with open(filepath, 'w', encoding='utf-8') as file:
                            file.write(new_content)
                        print(f"Refactored: {filepath}")
                except Exception as e:
                    print(f"Error reading {filepath}: {e}")

if __name__ == '__main__':
    refactor_dir('F:/Gravity_AI_bridge')
