import glob
import os

for filepath in glob.glob("wiki/*.md"):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()
        
    new_content = content.replace("V16.6 PRO", "V16.7 PRO").replace("V16.6", "V16.7")
    
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(new_content)
        
print("Wiki actualizada exitosamente.")
