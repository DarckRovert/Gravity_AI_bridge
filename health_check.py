"""
health_check.py — Diagnóstico V2.1 Multi-Modelo
Verifica inventario local de Ollama y estado de la sesión.
"""

import urllib.request
import json
import os
import sys

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()
BASE_DIR = os.path.dirname(__file__)
SETTINGS_FILE = os.path.join(BASE_DIR, "_settings.json")
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f: return json.load(f)
    return {"last_model": "deepseek-r1:8b"}

def get_ollama_inventory():
    try:
        with urllib.request.urlopen(OLLAMA_TAGS_URL, timeout=3) as r:
            return json.loads(r.read().decode())["models"]
    except: return None

def main():
    console.print(Panel("[bold cyan]🔍 GRAVITY AI BRIDGE — DIAGNÓSTICO V2.1[/]", border_style="cyan"))
    
    settings = load_settings()
    pref_model = settings.get("last_model")
    models = get_ollama_inventory()
    
    if models is None:
        console.print("[bold red]✗ ERROR:[/] Ollama no está corriendo localmente.")
        sys.exit(1)
        
    all_ok = False
    table = Table(title="📦 Inventario de Modelos Locales", box=box.ROUNDED, border_style="dim")
    table.add_column("Modelo", style="bold white")
    table.add_column("Estado", justify="center")
    table.add_column("Tamaño", justify="right")
    
    for m in models:
        m_name = m['name']
        is_pref = m_name == pref_model
        if is_pref: all_ok = True
        
        status = "[bold green]✓ Preferido[/]" if is_pref else "[dim]Disponible[/]"
        size = f"{m['size']/1024**3:.2f} GB"
        table.add_row(m_name, status, size)
        
    console.print(table)
    
    if not all_ok:
        console.print(f"[bold yellow]⚠ PRECAUCIÓN:[/] Tu modelo preferido '[bold cyan]{pref_model}[/]' no fue encontrado en Ollama.")
        if models: console.print(f"[dim]El Auditor te pedirá elegir uno de la lista al iniciar.[/]")
    else:
        console.print(f"[bold green]✅ LISTO:[/] Sistema configurado con [bold yellow]{pref_model}[/].")

if __name__ == "__main__":
    main()
