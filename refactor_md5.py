import glob

files_to_check = glob.glob('F:/Gravity_AI_bridge/**/*.py', recursive=True)

for filepath in files_to_check:
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
        
    new_content = content.replace("hashlib.sha256(", "hashlib.sha256(").replace("_hl.sha256(", "_hl.sha256(")
    
    if new_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Refactored: {filepath}")
