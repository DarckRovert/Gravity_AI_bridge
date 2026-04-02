"""
health_check.py — Diagnóstico del sistema Gravity AI Bridge
Verifica que todos los componentes estén operativos antes de iniciar el Auditor.
"""

import urllib.request
import urllib.error
import json
import sys
import time

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import box

console = Console()
OLLAMA_TAGS_URL = "http://localhost:11434/api/tags"
REQUIRED_MODEL = "deepseek-r1:8b"


def check_ollama_running() -> tuple[bool, str]:
    """Verifica si el servidor Ollama está activo."""
    try:
        start = time.monotonic()
        with urllib.request.urlopen(OLLAMA_TAGS_URL, timeout=5) as resp:
            latency_ms = int((time.monotonic() - start) * 1000)
            if resp.status == 200:
                return True, f"{latency_ms} ms"
    except urllib.error.URLError:
        pass
    return False, "—"


def check_model_available() -> tuple[bool, list[str]]:
    """Verifica si el modelo requerido está descargado en Ollama."""
    try:
        with urllib.request.urlopen(OLLAMA_TAGS_URL, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            models = [m["name"] for m in data.get("models", [])]
            is_available = any(REQUIRED_MODEL in m for m in models)
            return is_available, models
    except Exception:
        return False, []


def check_python_deps() -> list[tuple[str, bool, str]]:
    """Verifica las dependencias de Python necesarias."""
    deps = []
    for pkg, import_name in [("rich", "rich"), ("json", "json"), ("urllib", "urllib")]:
        try:
            __import__(import_name)
            deps.append((pkg, True, "✓ Instalado"))
        except ImportError:
            deps.append((pkg, False, "✗ Falta"))
    return deps


def main():
    console.clear()
    console.print(
        Panel(
            "[bold cyan]🔍 GRAVITY AI BRIDGE — DIAGNÓSTICO DEL SISTEMA[/]\n"
            "[dim]Verificando todos los componentes antes de iniciar el Auditor...[/]",
            border_style="cyan",
            padding=(1, 2),
        )
    )

    all_ok = True

    # ─── Check 1: Ollama
    console.print("\n[bold yellow][ 1/3 ] Verificando Ollama...[/]")
    ollama_ok, latency = check_ollama_running()
    if ollama_ok:
        console.print(f"  [bold green]✓[/] Ollama está corriendo. Latencia: [cyan]{latency}[/]")
    else:
        console.print(
            "  [bold red]✗ Ollama no responde.[/] Inicia el servicio con:\n"
            "    [dim]ollama serve[/]"
        )
        all_ok = False

    # ─── Check 2: Modelo
    console.print("\n[bold yellow][ 2/3 ] Verificando modelo...[/]")
    if ollama_ok:
        model_ok, available_models = check_model_available()
        if model_ok:
            console.print(f"  [bold green]✓[/] Modelo [cyan]{REQUIRED_MODEL}[/] disponible.")
        else:
            console.print(
                f"  [bold red]✗ Modelo {REQUIRED_MODEL} no encontrado.[/] Descárgalo con:\n"
                f"    [dim]ollama pull {REQUIRED_MODEL}[/]"
            )
            if available_models:
                console.print(f"  [dim]Modelos disponibles: {', '.join(available_models)}[/]")
            all_ok = False
    else:
        console.print("  [dim]Saltado (Ollama no disponible).[/]")

    # ─── Check 3: Dependencias Python
    console.print("\n[bold yellow][ 3/3 ] Verificando dependencias Python...[/]")
    deps = check_python_deps()
    dep_table = Table(box=box.SIMPLE, show_header=True, header_style="bold white")
    dep_table.add_column("Paquete", style="cyan")
    dep_table.add_column("Estado", style="white")
    for pkg, ok, status in deps:
        style = "green" if ok else "red"
        dep_table.add_row(pkg, f"[{style}]{status}[/{style}]")
        if not ok:
            all_ok = False
    console.print(dep_table)

    # ─── Resumen Final
    console.print()
    if all_ok:
        console.print(
            Panel(
                "[bold green]✅ SISTEMA LISTO.[/]\n"
                "Todos los componentes están operativos. Puedes iniciar el Auditor.",
                border_style="green",
                padding=(1, 2),
            )
        )
        sys.exit(0)
    else:
        console.print(
            Panel(
                "[bold red]❌ SISTEMA NO LISTO.[/]\n"
                "Corrige los errores indicados antes de iniciar el Auditor Senior.",
                border_style="red",
                padding=(1, 2),
            )
        )
        sys.exit(1)


if __name__ == "__main__":
    main()
