"""
Gravity AI — Diagnóstico y Diagnóstico del Ecosistema de Proveedores (Health Check CLI)
Estándar: Diamond-Tier (Tipado formal riguroso, resiliencia extrema en puertos/sockets y UI hermosa).
"""

import os
import sys
import json
import socket
from typing import List, Dict, Any, Optional, Union

from rich.console import Console
from rich.table import Table
from rich import box
from rich.panel import Panel
from rich.text import Text
from rich.align import Align

try:
    import pyfiglet
except ImportError:
    pyfiglet = None

from core import provider_manager

# ── Resiliencia de Consola UTF-8 en Entornos Windows ──────────────────────────
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        import io

        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

import threading

console: Console = Console()
SETTINGS_FILE: str = os.path.join(os.path.dirname(__file__), "_settings.json")
_settings_lock: threading.RLock = threading.RLock()


def load_settings() -> Dict[str, Any]:
    """
    Carga las configuraciones del modelo activo y proveedor desde el almacenamiento _settings.json.
    Operación protegida mediante RLock de exclusión mutua para soporte multihilo extremo.

    Retorna:
        Dict[str, Any]: Diccionario con las opciones cargadas o por defecto ante fallos.
    """
    default_settings: Dict[str, Any] = {
        "last_model": "deepseek-r1:8b",
        "provider": "ollama",
        "provider_protocol": "ollama",
        "api_url": "http://localhost:11434",
    }
    with _settings_lock:
        if os.path.exists(SETTINGS_FILE):
            try:
                with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                    loaded: Dict[str, Any] = json.load(f)
                    if isinstance(loaded, dict) and "provider" in loaded:
                        return loaded
            except Exception:
                console.print(
                    "[bold red]⚠ Advertencia:[/] _settings.json está corrompido o inaccesible. Cargando valores por defecto."
                )
        return default_settings


def save_settings(data: Dict[str, Any]) -> None:
    """
    Guarda de forma atómica y segura las opciones actuales del sistema en _settings.json.
    Garantiza thread-safety y resiliencia en sistemas Windows mediante exclusión mutua.

    Parámetros:
        data (Dict[str, Any]): Parámetros del proveedor a serializar.
    """
    with _settings_lock:
        temp_file: str = SETTINGS_FILE + ".tmp"
        try:
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

            # Reemplazo seguro atómico tolerante a bloqueos de Windows
            if os.path.exists(SETTINGS_FILE):
                try:
                    os.remove(SETTINGS_FILE)
                except OSError:
                    pass  # Continuar si ya está liberado o controlado

            os.rename(temp_file, SETTINGS_FILE)
        except Exception as e:
            console.print(
                f"[bold red]⚠ Error al guardar configuraciones de forma concurrente:[/] {str(e)}"
            )
            # Intento de limpieza de temporales
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except OSError:
                    pass


def draw_dashboard(results: List[Any]) -> None:
    """
    Renderiza una interfaz CLI enriquecida mediante tablas y paneles visuales
    que indican el estado de salud de todos los motores locales y cloud.

    Parámetros:
        results (List[Any]): Lista de proveedores escaneados del provider_manager.
    """
    table: Table = Table(
        title="📡 MAPA DE PROVEEDORES (LOCAL + CLOUD)",
        box=box.HEAVY_EDGE,
        border_style="cyan",
        title_style="bold bright_white",
    )
    table.add_column("Motor", style="bold white")
    table.add_column("Tier", justify="center")
    table.add_column("Estado", justify="center")
    table.add_column("Ping", justify="right")
    table.add_column("Modelo destacado", justify="left")

    for r in results:
        motor_name: str = r.name
        tier: str = (
            "☁ Cloud" if getattr(r, "category", "local") == "cloud" else "💻 Local"
        )

        if r.is_healthy:
            status: str = f"[bold green][OK] ACTIVO ({r.model_count}M)[/]"
            ping: str = f"{r.response_ms}ms"
            if r.active_model:
                motor_name = f"[OPTIMIZER] {r.name}"
                model_str: str = f"[bold yellow]{r.active_model} (Loaded)[/]"
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

        table.add_row(motor_name, tier, status, ping, model_str)

    console.print(Align.center(table))

    # ── Módulo FabricaWeb (Puerto 3000) ──
    s: socket.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.5)
    fw_status: str = "[bold red]offline[/]"
    try:
        # Intenta conexión segura al puerto 3000
        if s.connect_ex(("127.0.0.1", 3000)) == 0:
            fw_status = "[bold green]ONLINE[/]"
    except Exception:
        pass
    finally:
        s.close()

    console.print(
        Align.center(
            Panel(
                f"💎 [bold white]Estatus de Módulos Especiales:[/] FabricaWeb (Next.js): {fw_status}",
                border_style="dim",
                padding=(0, 2),
            )
        )
    )


def prompt_menu(results: List[Any]) -> Optional[Union[str, Any]]:
    """
    Muestra un menú interactivo en consola para seleccionar manualmente
    cuál motor activo debe actuar como proxy de inferencia.

    Parámetros:
        results (List[Any]): Lista de proveedores activos.

    Retorna:
        Optional[Union[str, Any]]: El proveedor seleccionado o "AUTO".
    """
    healthy: List[Any] = [r for r in results if r.is_healthy and r.models]
    if len(healthy) < 2:
        return None

    console.print()
    console.print(
        Panel(
            "[bold bright_white]Múltiples motores en línea detectados.[/]\nElige tu proxy de inferencia:",
            border_style="yellow",
        )
    )

    for i, r in enumerate(healthy, 1):
        mod: str = r.active_model or r.models[0]["name"]
        tag: str = "[bold yellow](En Memoria)[/]" if r.active_model else ""
        tier: str = (
            "[Cloud]" if getattr(r, "category", "local") == "cloud" else "[Local]"
        )
        console.print(f"  [bold cyan][{i}][/] {tier} {r.name:<12} -> {mod} {tag}")

    console.print(
        f"  [bold cyan][{len(healthy) + 1}][/] Auto-Selección Inteligente (Recomendado)"
    )

    # Asegurar uso de readline en Windows para estética
    try:
        import pyreadline3  # noqa: F401
    except ImportError:
        pass

    from rich.prompt import Prompt

    while True:
        try:
            choice: str = Prompt.ask(
                "\n>> Elige una opción",
                choices=[str(x) for x in range(1, len(healthy) + 2)],
            )
            idx: int = int(choice) - 1
            if idx == len(healthy):
                return "AUTO"
            return healthy[idx]
        except Exception:
            pass


def main() -> None:
    """
    Punto de entrada principal para el diagnóstico integral de la plataforma.
    Escanea los proveedores, evalúa la latencia y actualiza el settings.json global.
    """
    try:
        if pyfiglet:
            f_logo: str = pyfiglet.figlet_format("GRAVITY AI", font="doom")
            console.print(Align.center(f"[bold bright_cyan]{f_logo}[/]"))
    except Exception:
        pass

    console.print(
        Align.center(
            Panel(
                Text(
                    "SISTEMA DE DIAGNÓSTICO V13.0 PRO",
                    justify="center",
                    style="bold bright_white",
                ),
                style="on bright_black",
                box=box.HEAVY_EDGE,
                padding=(0, 2),
            )
        )
    )

    with console.status(
        "[bold cyan]⏳ Escaneando ecosistema Local y Cloud (RTO)...[/]", spinner="dots"
    ):
        scans: List[Any] = provider_manager.scan_all()

    healthy_count: int = sum(1 for s in scans if s.is_healthy)
    if healthy_count == 0:
        draw_dashboard(scans)
        console.print(
            "\n[bold red]✖ ERROR CRÍTICO:[/] No se detectó ningún proveedor de IA (Ollama, LM Studio o Keys de Cloud) activo."
        )
        console.print(
            "[yellow]Por favor, inicia un motor local o usa key_manager.py para añadir claves e inténtalo de nuevo.[/]"
        )
        sys.exit(1)

    settings: Dict[str, Any] = load_settings()

    # Evaluar proveedor actual
    current_prov: Optional[Any] = next(
        (
            s
            for s in scans
            if s.protocol == settings.get("provider_protocol") and s.is_healthy
        ),
        None,
    )
    if not current_prov:
        current_prov = next(
            (s for s in scans if s.name == settings.get("provider") and s.is_healthy),
            None,
        )

    draw_dashboard(scans)

    best_prov: Any
    best_mod: str
    best_prov, best_mod = provider_manager.get_best()

    chosen_prov: Optional[Any] = current_prov
    chosen_mod: str = settings.get("last_model", "deepseek-r1:8b")

    healthy: List[Any] = [r for r in scans if r.is_healthy]

    if len(healthy) > 1:
        user_choice: Optional[Union[str, Any]] = prompt_menu(scans)
        if user_choice == "AUTO":
            chosen_prov = best_prov
            chosen_mod = best_mod
        elif user_choice:
            chosen_prov = user_choice
            chosen_mod = user_choice.active_model or user_choice.models[0]["name"]
    elif not current_prov:
        console.print(
            f"\n[dim yellow][OPTIMIZER] Proveedor actual no encontrado. Cambiando a {best_prov.name}...[/]"
        )
        chosen_prov = best_prov
        chosen_mod = best_mod

    if chosen_prov:
        model_exists: bool = any(m["name"] == chosen_mod for m in chosen_prov.models)
        if not model_exists:
            chosen_mod = chosen_prov.active_model or chosen_prov.models[0]["name"]

        settings["provider"] = chosen_prov.name
        settings["provider_protocol"] = chosen_prov.protocol
        settings["api_url"] = chosen_prov.url
        settings["last_model"] = chosen_mod
        save_settings(settings)

        console.print(
            f"\n[bold green][OK] LISTO:[/] Conectado a [bold cyan]{chosen_prov.name}[/] usando [bold yellow]{chosen_mod}[/]."
        )
    else:
        console.print("\n[bold red]Error al determinar proveedor.[/]")
        sys.exit(1)


if __name__ == "__main__":
    main()
