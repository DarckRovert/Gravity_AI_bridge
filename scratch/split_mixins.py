import os
import re

BASE_DIR = r"f:\Gravity_AI_bridge"
MIXIN_POST = os.path.join(BASE_DIR, "api", "routes", "mixin_post.py")
MIXIN_GET = os.path.join(BASE_DIR, "api", "routes", "mixin_get.py")

ROUTERS_DIR = os.path.join(BASE_DIR, "api", "routers")
os.makedirs(ROUTERS_DIR, exist_ok=True)

# We will classify routes into categories based on URL
def get_category(path):
    if "chat/completions" in path or "gravity/chat" in path or "model/lock" in path: return "chat"
    if "youtube" in path or "video" in path or "obs" in path or "image" in path or "fooocus" in path or "v2v" in path: return "media"
    if "gameserver" in path: return "gameserver"
    if "rag" in path or "tools" in path or "agent" in path or "journalist" in path or "bounties" in path or "infiltrator" in path: return "agent"
    return "system"

def process_file(filepath, method_name, http_method):
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Find the start of the method (do_POST or do_GET)
    start_idx = -1
    for i, line in enumerate(lines):
        if line.strip().startswith(f"def {method_name}(self):"):
            start_idx = i
            break
            
    if start_idx == -1: return
    
    # Extract blocks based on `if self.path`
    routes = []
    current_route = None
    current_block = []
    
    # A simple state machine
    for line in lines[start_idx+1:]:
        stripped = line.strip()
        # Detect new route
        match = re.match(r'^if\s+self\.path(?:\.split\("\?"\)\[0\])?\s*==\s*[\'"]([^\'"]+)[\'"]\s*:', stripped)
        if match:
            if current_route:
                routes.append((current_route, current_block))
            current_route = match.group(1)
            current_block = [line]
            continue
            
        match_start = re.match(r'^if\s+self\.path\.startswith\([\'"]([^\'"]+)[\'"]\)\s*:', stripped)
        if match_start:
            if current_route:
                routes.append((current_route, current_block))
            current_route = match_start.group(1) + "{full_path:path}" # FastAPI wildcard
            current_block = [line]
            continue
            
        # Detect `def _serve...` (in mixin_get)
        match_def = re.match(r'^def\s+_serve_([a-zA-Z0-9_]+)\(self\):', stripped)
        if match_def:
            if current_route:
                routes.append((current_route, current_block))
            current_route = f"/{match_def.group(1)}" # dummy route name
            current_block = [line]
            continue
            
        if current_route:
            current_block.append(line)

    if current_route:
        routes.append((current_route, current_block))
        
    print(f"Extracted {len(routes)} routes from {filepath}")
    return routes

routes_post = process_file(MIXIN_POST, "do_POST", "post")
routes_get = process_file(MIXIN_GET, "do_GET", "get") # Not exact, as mixin_get uses routing dict

print("Found POST routes:", len(routes_post) if routes_post else 0)
