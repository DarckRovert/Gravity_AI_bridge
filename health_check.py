import os
import sys
import json
import time

from rich.console import Console
from rich.table import Table
from rich import box
from rich.panel import Panel
from rich.text import Text
from rich.align import Align
import pyfiglet

from provider_scanner import ProviderScanner

console = Console()
SETTINGS_FILE = os.path.join(os.path.dirname(__file__), "_settings.json")

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except Exception:
            console.print("[bold red]⚠ Advertencia:[/] _settings.json está corrompido. Cargando valores por defecto.")
    return {"last_model": "deepseek-r1:8b", "provider": "ollama", "api_url": "http://localhost:11434"}

def save_settings(data):
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

def draw_dashboard(results):
    table = Table(title="📡 MAPA DE PROVEEDORES LOCALES", box=box.HEAVY_EDGE, border_style="cyan", title_style="bold bright_white")
    table.add_column("Motor", style="bold white")
    table.add_column("Puerto", justify="center")
    table.add_column("Estado", justify="center")
    table.add_column("Ping", justify="right")
    table.add_column("Modelo destacado", justify="left")
    
    for r in results:
        motor_name = r.name
        port = r.url.split(":")[-1]
        
        if r.is_healthy:
            status = f"[bold green]✅ ACTIVO ({r.model_count}M)[/]"
            ping = f"{r.response_ms}ms"
            if r.active_model:
                motor_name = f"⚡ {r.name}"
                model_str = f"[bold yellow]{r.active_model} (GPU)[/]"
            elif r.model_count > 0:
                motor_name = r.name
                model_str = f"[dim]{r.models[0]['name']}[/]"
            else:
                model_str = "[dim]Sin modelos[/]"
        else:
            status = "[dim red]🔴 Inactivo[/]"
            ping = "[dim]—[/]"
            model_str = "[dim]—[/]"
            motor_name = f"[dim]{r.name}[/]"
            
        table.add_row(motor_name, port, status, ping, model_str)
        
    console.print(Align.center(table))

def prompt_menu(results):
    healthy = [r for r in results if r.is_healthy and r.models]
    if len(healthy) < 2:
        return None # No menu needed
        
    console.print()
    console.print(Panel("[bold bright_white]Múltiples motores en línea detectados.[/]\nElige tu proxy de inferencia:", border_style="yellow"))
    
    for i, r in enumerate(healthy, 1):
        mod = r.active_model or r.models[0]['name']
        tag = "[bold yellow](Cargado en GPU)[/]" if r.active_model else ""
        console.print(f"  [bold cyan][{i}][/] {r.name:<12} -> {mod} {tag}")
        
    console.print(f"  [bold cyan][{len(healthy)+1}][/] Auto-Selección Inteligente (Recomendado)")
    
    try:
        import pyreadline3 # To enable good prompt in windows
    except: pass
    from rich.prompt import Prompt
    while True:
        try:
            choice = Prompt.ask("\n>> Elige una opción", choices=[str(i) for i in range(1, len(healthy)+2)])
            idx = int(choice) - 1
            if idx == len(healthy):
                return "AUTO"
            return healthy[idx]
        except:
            pass

def main():
    try:
        f_logo = pyfiglet.figlet_format("GRAVITY AI", font="doom")
        console.print(Align.center(f"[bold bright_cyan]{f_logo}[/]"))
    except Exception:
        pass
        
    console.print(Align.center(Panel(Text("SISTEMA DE DIAGNÓSTICO V5.1", justify="center", style="bold bright_white"), style="on bright_black", box=box.HEAVY_EDGE, padding=(0,2))))
    
    with console.status("[bold cyan]⏳ Escaneando ecosistema de IA local en paralelo...[/]", spinner="dots"):
        scans = ProviderScanner.scan_all()
        
    healthy_count = sum(1 for s in scans if s.is_healthy)
    if healthy_count == 0:
        draw_dashboard(scans)
        console.print("\n[bold red]✖ ERROR CRÍTICO:[/] No se detectó ningún proveedor de IA (Ollama, LM Studio) en ejecución.")
        console.print("[yellow]Por favor, inicia Ollama o LM Studio e inténtalo de nuevo.[/]")
        sys.exit(1)
        
    settings = load_settings()
    
    # Check if current provider is dead, or if multiple exist
    current_prov = next((s for s in scans if s.protocol == settings.get("provider") and s.is_healthy), None)
    
    draw_dashboard(scans)
    
    best_prov, best_mod = ProviderScanner.auto_select_best(scans)
    
    # Si hay múltiples proveedores sanos, preguntamos. Sino, tomamos current o el mejor si current murio.
    chosen_prov = current_prov
    chosen_mod = settings.get("last_model")
    
    healthy = [r for r in scans if r.is_healthy]
    
    if len(healthy) > 1:
        user_choice = prompt_menu(scans)
        if user_choice == "AUTO":
            chosen_prov = best_prov
            chosen_mod = best_mod
        elif user_choice:
            chosen_prov = user_choice
            chosen_mod = user_choice.active_model or user_choice.models[0]['name']
    elif not current_prov:
        console.print(f"\n[dim yellow]⚡ Proveedor actual no encontrado. Cambiando a {best_prov.name}...[/]")
        chosen_prov = best_prov
        chosen_mod = best_mod
        
    # Verificar si el model elegido sigue existiendo en el chosen_prov
    if chosen_prov:
        model_exists = any(m['name'] == chosen_mod for m in chosen_prov.models)
        if not model_exists:
            chosen_mod = chosen_prov.active_model or chosen_prov.models[0]['name']
            
        settings["provider"] = chosen_prov.protocol
        port = chosen_prov.url.split(":")[-1]
        settings["api_url"] = f"http://localhost:{port}"
        settings["last_model"] = chosen_mod
        save_settings(settings)
        
        console.print(f"\n[bold green]✅ LISTO:[/] Sistema conectado a [bold cyan]{chosen_prov.name}[/] usando [bold yellow]{chosen_mod}[/].")
    else:
        console.print("\n[bold red]Error al determinar proveedor.[/]")
        sys.exit(1)

if __name__ == "__main__":
    main()
