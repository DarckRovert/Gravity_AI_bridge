import os

def standardize_python_header(path, title_main, title_sub):
    if not os.path.exists(path): 
        print(f"Skipping: {path}")
        return
    
    # Marco de 80 caracteres de ancho
    top    = '╔' + ('═' * 78) + '╗'
    bottom = '╚' + ('═' * 78) + '╝'
    
    p1 = (78 - len(title_main)) // 2
    p2 = 78 - len(title_main) - p1
    line1 = '║' + (' ' * p1) + title_main + (' ' * p2) + '║'
    
    p3 = (78 - len(title_sub)) // 2
    p4 = 78 - len(title_sub) - p3
    line2 = '║' + (' ' * p3) + title_sub + (' ' * p4) + '║'
    
    with open(path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    if len(lines) < 5 or not '╔' in lines[1]:
        print(f"No valid header found in: {path}")
        return

    new_lines = []
    new_lines.append('"""\n')
    new_lines.append(top + '\n')
    new_lines.append(line1 + '\n')
    new_lines.append(line2 + '\n')
    new_lines.append(bottom + '\n')
    new_lines.append('"""\n')
    
    # Saltar el encabezado antiguo (hasta las segundas tri-comillas)
    i = 5
    while i < len(lines) and '"""' not in lines[i]:
        i += 1
    
    # Añadir el resto del archivo
    new_lines.extend(lines[min(i+1, len(lines)):])
    
    with open(path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print(f'SYMMETRY FIXED: {path}')

if __name__ == "__main__":
    base = "F:/Gravity_AI_bridge"
    targets = [
        (f"{base}/INSTALAR.py", "GRAVITY AI BRIDGE - INSTALADOR STANDALONE V9.0 PRO [Diamond-Tier Edition]", "Instalador TUI premium con elección de directorio"),
        (f"{base}/ask_deepseek.py", "GRAVITY AI BRIDGE - AUDITOR SENIOR V9.0 PRO [Diamond-Tier Edition]", "CLI Frontend | RAG | Tools | Multi-model"),
        (f"{base}/bridge_server.py", "GRAVITY AI - BRIDGE SERVER V9.0 PRO [Diamond-Tier Edition]", "Enrutador Universal OpenAI-Compatible"),
        (f"{base}/core/data_guardian.py", "GRAVITY AI - DATA GUARDIAN V9.0 PRO [Diamond-Tier Edition]", "Validación, reparación y saneamiento de archivos de datos"),
        (f"{base}/core/session_manager.py", "GRAVITY AI - SESSION MANAGER V9.0 PRO [Diamond-Tier Edition]", "Sesiones con Fork/Merge + Export"),
        (f"{base}/core/cache_engine.py", "GRAVITY AI - CACHE ENGINE V9.0 PRO [Diamond-Tier Edition]", "Optimized with WAL mode and Reasoning-Aware Hashing"),
        (f"{base}/core/cost_tracker.py", "GRAVITY AI - COST TRACKER V9.0 PRO [Diamond-Tier Edition]", "Tracking de costes cloud en tiempo real"),
        (f"{base}/core/provider_manager.py", "GRAVITY AI - PROVIDER MANAGER V9.0 PRO [Diamond-Tier Edition]", "Orquestador universal: local + cloud")
    ]
    
    for path, t1, t2 in targets:
        standardize_python_header(path, t1, t2)
