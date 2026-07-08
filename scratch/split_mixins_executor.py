import os
import re

BASE_DIR = r"f:\Gravity_AI_bridge"
MIXIN_POST = os.path.join(BASE_DIR, "api", "routes", "mixin_post.py")
OUT_DIR = os.path.join(BASE_DIR, "api", "routes")

def get_category(path):
    path = path.lower()
    if "chat/completions" in path or "gravity/chat" in path or "model/lock" in path or "/keys" in path or "language/clone" in path: return "chat"
    if "youtube" in path or "video" in path or "obs" in path or "image" in path or "fooocus" in path or "v2v" in path or "social" in path or "affiliate" in path or "revenue" in path: return "media"
    if "gameserver" in path: return "gameserver"
    if "rag" in path or "tools" in path or "agent" in path or "journalist" in path or "bounties" in path or "infiltrator" in path or "factory" in path or "hitl" in path or "reflection" in path or "autonomy" in path: return "agent"
    return "system"

def main():
    with open(MIXIN_POST, "r", encoding="utf-8") as f:
        lines = f.readlines()

    start_idx = -1
    for i, line in enumerate(lines):
        if line.strip().startswith("def do_POST(self):"):
            start_idx = i
            break
            
    header_lines = lines[:start_idx]
    
    routes = []
    current_route = None
    current_block = []
    
    for line in lines[start_idx+1:]:
        stripped = line.strip()
        match = re.match(r'^if\s+self\.path(?:\.split\("\?"\)\[0\])?\s*==\s*[\'"]([^\'"]+)[\'"]\s*:', stripped)
        if match:
            if current_route: routes.append((current_route, current_block))
            current_route = match.group(1)
            current_block = [line]
            continue
            
        match_start = re.match(r'^if\s+self\.path\.startswith\([\'"]([^\'"]+)[\'"]\)\s*:', stripped)
        if match_start:
            if current_route: routes.append((current_route, current_block))
            current_route = match_start.group(1)
            current_block = [line]
            continue
            
        if current_route:
            current_block.append(line)

    if current_route:
        routes.append((current_route, current_block))
        
    categories = {"chat": [], "media": [], "gameserver": [], "agent": [], "system": []}
    
    for route_path, block in routes:
        cat = get_category(route_path)
        categories[cat].append(block)
        
    for cat, blocks in categories.items():
        if not blocks: continue
        class_name = f"Post{cat.capitalize()}Mixin"
        out_file = os.path.join(OUT_DIR, f"mixin_post_{cat}.py")
        
        with open(out_file, "w", encoding="utf-8") as f:
            f.writelines(header_lines)
            f.write(f"\nclass {class_name}:\n")
            f.write(f"    def _handle_post_{cat}(self):\n")
            
            for block in blocks:
                # We need to replace the 'return' with 'return True' so the router knows it handled it.
                # And the end of the block needs a return True if it doesn't have one? No, Gravity code always ends with return.
                # So we just replace `return` with `return True` if it's returning empty.
                for line in block:
                    if line.strip() == "return":
                        f.write(line.replace("return", "return True"))
                    else:
                        f.write(line)
            f.write("        return False\n")
            print(f"Generated {out_file} with {len(blocks)} endpoints.")

if __name__ == "__main__":
    main()
