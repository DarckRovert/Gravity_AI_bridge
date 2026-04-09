"""
╔══════════════════════════════════════════════════════════════════════════════╗
║  GRAVITY AI BRIDGE - INSTALADOR STANDALONE V9.0 PRO [Diamond-Tier Edition]   ║
║              Instalador TUI premium con elección de directorio               ║
╚══════════════════════════════════════════════════════════════════════════════╝
"""

import sys
import os
import subprocess
import shutil
import json
import time
import ctypes
import glob
import platform
from datetime import datetime
from pathlib import Path

# ── Bootstrap Rich antes de continuar ─────────────────────────────────────────
def _bootstrap():
    pkgs = ["rich", "pyfiglet", "pyreadline3"]
    for pkg in pkgs:
        try:
            __import__(pkg)
        except ImportError:
            print(f"  Instalando {pkg}...", flush=True)
            subprocess.run(
                [sys.executable, "-m", "pip", "install", pkg, "-q",
                 "--no-warn-script-location"],
                check=True, capture_output=True
            )

_bootstrap()

from rich.console   import Console
from rich.panel     import Panel
from rich.progress  import Progress, SpinnerColumn, BarColumn, TextColumn, TimeElapsedColumn
from rich.table     import Table
from rich.prompt    import Prompt, Confirm
from rich.columns   import Columns
from rich.align     import Align
from rich.text      import Text
from rich           import box
import pyfiglet

console    = Console()
APP_VER    = "9.0 PRO"
SOURCE_DIR = os.path.dirname(os.path.abspath(__file__))

# ── Archivos/Dirs a EXCLUIR de la distribución ────────────────────────────────
# Estos son artefactos de desarrollo, datos de runtime o datos personales.
EXCLUDE_FILES = {
    # Runtime data (se regeneran automáticamente)
    "_audit_log.jsonl", "_cache.sqlite", "_cache.sqlite-shm",
    "_cache.sqlite-wal", "_cost_log.json", "_history.json",
    "_last_scan.json", "_settings.json", "bridge.log", "config.yaml",
    "_first_run_done", "_knowledge.json",
    # Artefactos del instalador mismo
    "_install_manifest.json",
    # Archivos del entorno del desarrollador (no distribuir)
    "%VBS_PATH%", "_check_dist.py",
}

EXCLUDE_DIRS = {
    ".git", "__pycache__", "_saves", "_rag_index",
    ".agents", "dev_utils", "tests"
}

EXCLUDE_EXTENSIONS = {".pyc", ".pyo", ".bak", ".tmp"}
EXCLUDE_PATTERNS   = ("*.bak_*", "*.sqlite-*")

# ── Componentes obligatorioes ─────────────────────────────────────────────────────
COMPONENTS = {
    "rag_pdf": {
        "label": "Soporte PDF en RAG",
        "desc":  "Indexar archivos PDF como contexto (requiere pypdf)",
        "pkgs":  ["pypdf"],
        "default": True,
    },
    "cloud_ai": {
        "label": "Proveedores Cloud (OpenAI · Anthropic · Google · Groq)",
        "desc":  "APIs cloud con cifrado de keys DPAPI",
        "pkgs":  ["anthropic", "google-generativeai"],
        "default": True,
    },
    "mcp": {
        "label": "MCP - Model Context Protocol",
        "desc":  "Conexión a servidores de herramientas externos",
        "pkgs":  ["mcp"],
        "default": False,
    },
    "observability": {
        "label": "Métricas Prometheus (/metrics endpoint)",
        "desc":  "Monitorización del bridge compatible con Prometheus",
        "pkgs":  ["prometheus_client"],
        "default": False,
    },
}

CORE_PKGS = [
    "rich", "pyfiglet", "pyreadline3", "pyyaml", "httpx",
    "requests", "psutil",
]


# ══════════════════════════════════════════════════════════════════════════════
# PANTALLA DE BIENVENIDA
# ══════════════════════════════════════════════════════════════════════════════

def phase_welcome():
    console.clear()
    fig = pyfiglet.Figlet(font="slant")
    title = fig.renderText("GRAVITY AI").rstrip()
    console.print(f"[bold bright_cyan]{title}[/]")

    feat_table = Table(box=box.SIMPLE, show_header=False, padding=(0, 2))
    feat_table.add_column("", style="cyan",  width=3)
    feat_table.add_column("", style="white")
    features = [
        ("◈", "Enrutamiento dinámico: Local + Cloud (Ollama · LM Studio · OpenAI · Anthropic)"),
        ("◈", "CLI premium con 20+ comandos, RAG híbrido y MCP"),
        ("◈", "Dashboard web interactivo con streaming en tiempo real"),
        ("◈", "API 100% compatible OpenAI para Cursor, VS Code y Aider"),
        ("◈", "Audit log inmutable · Métricas Prometheus · Keys cifradas DPAPI"),
        ("◈", "Data Guardian: integridad de datos automática con backup atómico"),
        ("◈", "Instalación en cualquier directorio + acceso global 'gravity'"),
    ]
    for ico, desc in features:
        feat_table.add_row(ico, desc)

    console.print(Panel(
        feat_table,
        title=f"[bold bright_white] Gravity AI Bridge {APP_VER} - Instalador [/]",
        subtitle="[dim]github.com/DarckRovert/Gravity_AI_bridge[/]",
        border_style="cyan",
        box=box.DOUBLE,
        padding=(1, 3),
    ))
    console.print()


# ══════════════════════════════════════════════════════════════════════════════
# ELECCIÓN DE DIRECTORIO DE INSTALACIÓN
# ══════════════════════════════════════════════════════════════════════════════

def _default_install_dir() -> str:
    """Propone un directorio de instalación sensato según el SO."""
    if platform.system() == "Windows":
        local_app = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        return os.path.join(local_app, "GravityAI")
    return os.path.join(os.path.expanduser("~"), ".gravity_ai")


def phase_choose_directory(cli_dir: str = None, in_place: bool = False) -> str:
    """
    Muestra el selector de directorio de instalación.
    Retorna la ruta absoluta donde se instalará.
    """
    if cli_dir:
        target = os.path.abspath(cli_dir)
        console.print(f"[dim]Directorio de instalación (argumento): [bold]{target}[/][/]")
        return target

    if in_place:
        console.print(f"[dim]Instalación en sitio (modo desarrollo): [bold]{SOURCE_DIR}[/][/]")
        return SOURCE_DIR

    default = _default_install_dir()
    # Si ya hay una instalación en el directorio actual, ofrecerla como opción
    if os.path.exists(os.path.join(SOURCE_DIR, "_install_manifest.json")):
        default = SOURCE_DIR

    console.print(Panel(
        f"[bold white]¿Dónde deseas instalar Gravity AI Bridge?[/]\n\n"
        f"[dim]Por defecto:[/] [cyan]{default}[/]\n"
        f"[dim]Puedes escribir cualquier ruta absoluta. Se creará si no existe.[/]\n"
        f"[dim]Escribe '.' para instalar en el directorio actual:[/] [cyan]{SOURCE_DIR}[/]",
        title="[bold cyan]Directorio de Instalación[/]",
        border_style="blue",
        padding=(1, 2),
    ))
    console.print()

    while True:
        raw = Prompt.ask(
            "[bold cyan]Ruta de instalación[/]",
            default=default
        ).strip()

        if raw == ".":
            raw = SOURCE_DIR

        target = os.path.abspath(raw)

        # Verificar espacio disponible
        try:
            drive = Path(target).anchor or "."
            stat  = shutil.disk_usage(drive)
            free_mb = stat.free / (1024 * 1024)
            if free_mb < 500:
                console.print(f"[red]⚠ Solo {free_mb:.0f} MB libres en {drive}. Se necesitan mínimo 500 MB.[/]")
                continue
        except Exception:
            pass

        # Advertir si el directorio ya tiene contenido
        if os.path.exists(target) and os.listdir(target):
            has_manifest = os.path.exists(os.path.join(target, "_install_manifest.json"))
            if has_manifest:
                console.print(f"[yellow]  Instalación previa detectada en {target}. Se actualizará.[/]")
            else:
                console.print(f"[yellow]  El directorio ya existe y no está vacío.[/]")
            if not Confirm.ask("¿Continuar en este directorio?", default=True):
                continue

        console.print(f"\n[green]✓ Directorio seleccionado:[/] [bold]{target}[/]")
        console.print()
        return target


# ══════════════════════════════════════════════════════════════════════════════
# SELECCIÓN DE COMPONENTES
# ══════════════════════════════════════════════════════════════════════════════

def phase_components() -> dict:
    """Muestra selector de componentes. Retorna {component_id: bool}."""
    console.print(Panel(
        "[bold white]Selecciona los componentes a instalar.[/]\n"
        "[dim]El núcleo (Core) siempre se instala. Los demás son obligatorioes.[/]",
        title="[bold cyan]Componentes[/]",
        border_style="blue",
        padding=(1, 2),
    ))

    t = Table(box=box.SIMPLE_HEAD, padding=(0, 2))
    t.add_column("#",      style="dim",   width=3, justify="right")
    t.add_column("Componente", style="cyan")
    t.add_column("Descripción")
    t.add_column("Default", justify="center", width=8)

    t.add_row("0", "[bold green]Core[/]",
              "CLI · Bridge Server · Dashboard · Data Guardian · Providers",
              "[green]Siempre[/]")

    for i, (cid, meta) in enumerate(COMPONENTS.items(), 1):
        t.add_row(
            str(i), meta["label"], meta["desc"],
            "[green]✓[/]" if meta["default"] else "[dim]✗[/]"
        )

    console.print(t)
    console.print()

    selection = {}
    for i, (cid, meta) in enumerate(COMPONENTS.items(), 1):
        selection[cid] = Confirm.ask(
            f"  [{i}] ¿Instalar [cyan]{meta['label']}[/]?",
            default=meta["default"]
        )

    console.print()
    return selection


# ══════════════════════════════════════════════════════════════════════════════
# COPIA DE ARCHIVOS AL DESTINO
# ══════════════════════════════════════════════════════════════════════════════

def _should_exclude(name: str, is_dir: bool = False) -> bool:
    """Retorna True si el archivo/directorio debe ser excluido de la distribución."""
    if name in EXCLUDE_FILES:
        return True
    if is_dir and name in EXCLUDE_DIRS:
        return True
    if not is_dir and os.path.splitext(name)[1] in EXCLUDE_EXTENSIONS:
        return True
    for pat in EXCLUDE_PATTERNS:
        import fnmatch
        if fnmatch.fnmatch(name, pat):
            return True
    return False


def _collect_source_files() -> list[tuple[str, str]]:
    """
    Recorre SOURCE_DIR y devuelve lista de (src_abs, rel) de archivos a copiar.
    """
    result = []
    for root, dirs, files in os.walk(SOURCE_DIR):
        # Filtrar directorios excluidos (modifica dirs in-place para skip-walk)
        dirs[:] = [d for d in dirs if not _should_exclude(d, is_dir=True)]

        rel_root = os.path.relpath(root, SOURCE_DIR)

        for fname in files:
            if _should_exclude(fname):
                continue
            src = os.path.join(root, fname)
            rel = os.path.join(rel_root, fname) if rel_root != "." else fname
            result.append((src, rel))

    return result


def phase_copy_files(target_dir: str, progress: Progress) -> int:
    """
    Copia los archivos de distribución de SOURCE_DIR a target_dir.
    Retorna el número de archivos copiados.
    """
    if os.path.abspath(target_dir) == os.path.abspath(SOURCE_DIR):
        return 0  # Instalación in-place: nada que copiar

    files = _collect_source_files()
    task  = progress.add_task("[cyan]Copiando archivos...", total=len(files))
    copied = 0

    os.makedirs(target_dir, exist_ok=True)

    for src, rel in files:
        dst = os.path.join(target_dir, rel)
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        try:
            shutil.copy2(src, dst)
            copied += 1
        except Exception as e:
            console.print(f"[yellow]  Aviso al copiar {rel}: {e}[/]")
        finally:
            progress.advance(task)

    return copied


# ══════════════════════════════════════════════════════════════════════════════
# INSTALACIÓN DE DEPENDENCIAS
# ══════════════════════════════════════════════════════════════════════════════

def _pip_install(pkgs: list[str], progress: Progress, task_id) -> list[str]:
    """Instala paquetes con pip. Retorna lista de los que fallaron."""
    failed = []
    for pkg in pkgs:
        progress.update(task_id, description=f"[cyan]pip install {pkg}...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", pkg, "-q",
                 "--no-warn-script-location"],
                capture_output=True, text=True, timeout=120
            )
            if result.returncode != 0:
                failed.append(pkg)
        except Exception:
            failed.append(pkg)
        progress.advance(task_id)
    return failed


def phase_install_deps(components: dict, progress: Progress) -> list[str]:
    """Instala todas las dependencias. Retorna lista de paquetes fallidos."""
    all_pkgs = list(CORE_PKGS)
    for cid, enabled in components.items():
        if enabled:
            all_pkgs.extend(COMPONENTS[cid]["pkgs"])

    task = progress.add_task("[cyan]Instalando dependencias...", total=len(all_pkgs))
    return _pip_install(all_pkgs, progress, task)


# ══════════════════════════════════════════════════════════════════════════════
# DETECCIÓN DE HARDWARE
# ══════════════════════════════════════════════════════════════════════════════

def _detect_hardware() -> dict:
    hw = {
        "gpu_name": "Desconocida", "vram_mb": 0,
        "total_ram_mb": 0, "gpu_type": "cpu", "npu_name": None,
    }
    try:
        import psutil
        hw["total_ram_mb"] = round(psutil.virtual_memory().total / (1024**2))
    except Exception:
        pass

    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.total",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode == 0 and r.stdout.strip():
            parts = r.stdout.strip().split(",")
            hw["gpu_name"] = parts[0].strip()
            hw["vram_mb"]  = int(parts[1].strip())
            hw["gpu_type"] = "nvidia"
        return hw
    except Exception:
        pass

    try:
        r = subprocess.run(
            ["rocm-smi", "--showmeminfo", "vram", "--json"],
            capture_output=True, text=True, timeout=5
        )
        if r.returncode == 0:
            hw["gpu_type"] = "amd"
            hw["gpu_name"] = "AMD GPU"
        return hw
    except Exception:
        pass

    return hw


def _detect_local_engines() -> dict:
    import urllib.request as _ur
    found = {}
    for port, name in [
        (11434, "Ollama"), (1234, "LM Studio"),
        (8080, "KoboldCPP"), (8000, "vLLM"),
        (5001, "Jan AI"), (8888, "Lemonade"),
    ]:
        try:
            _ur.urlopen(f"http://localhost:{port}", timeout=1)
            found[name] = f"http://localhost:{port}"
        except Exception:
            pass
    return found


# ══════════════════════════════════════════════════════════════════════════════
# GENERACIÓN DE ARCHIVOS EN DESTINO
# ══════════════════════════════════════════════════════════════════════════════

def _generate_config(target_dir: str, hw: dict, engines: dict):
    """Genera config.yaml en el directorio de instalación.
    NO escribe un modelo por defecto: el sistema detecta el modelo cargado en runtime.
    """
    # Solo escribir proveedor si se detectó alguno; si no, dejar 'auto'
    if engines:
        default_prov = "ollama" if "Ollama" in engines else list(engines.keys())[0].lower().replace(" ", "_")
    else:
        default_prov = "auto"

    # Ctx size según VRAM
    vram = hw.get("vram_mb", 0)
    if vram >= 20000:
        ctx = 131072
    elif vram >= 10000:
        ctx = 65536
    elif vram >= 6000:
        ctx = 32768
    else:
        ctx = 16384

    config = f"""# Gravity AI Bridge V{APP_VER} - Configuración generada automáticamente
# Generado: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
# Edita este archivo para personalizar el comportamiento.
# NOTA: El modelo activo se detecta automáticamente del motor de IA en ejecución.
#       No es necesario especificar un modelo por defecto.

profile: production  # production | development

server:
  host: 0.0.0.0
  port: 7860
  log_level: INFO

model:
  default_provider: "{default_prov}"
  # default_model: null  ← déjalo comentado; Gravity auto-detecta el modelo cargado
  ctx_size: {ctx}
  temperature: 0.6
  top_p: 0.9
  stream: true

cache:
  enabled: true
  ttl_hours: 24

rate_limit:
  enabled: true
  requests_per_minute: 60
"""
    cfg_path = os.path.join(target_dir, "config.yaml")
    if not os.path.exists(cfg_path):
        with open(cfg_path, "w", encoding="utf-8") as f:
            f.write(config)



def _generate_gravity_bat(target_dir: str):
    """Genera gravity.bat en el directorio de instalación con rutas absolutas hardcodeadas."""
    content = f"""@echo off
cd /d "{target_dir}"
setlocal enabledelayedexpansion

REM ── Gravity AI Bridge V{APP_VER} - Comando Global ──────────────────────────────
REM Instalado en: {target_dir}
REM ────────────────────────────────────────────────────────────────────────────

if "%~1"=="--help" (
    echo.
    echo  GRAVITY AI BRIDGE V{APP_VER} - Ayuda Rapida
    echo  ─────────────────────────────────────────
    echo  gravity                  Modo interactivo
    echo  gravity "pregunta"       Respuesta directa por pipe
    echo  gravity --install        Reinstalar / actualizar
    echo  gravity --server         Iniciar bridge server
    echo  gravity --dashboard      Abrir dashboard (http://localhost:7860)
    echo  gravity --status         Estado de los motores de IA
    echo  gravity --version        Version actual
    echo  gravity --uninstall      Desinstalar
    echo.
    exit /b 0
)

if "%~1"=="--version" (
    echo Gravity AI Bridge V{APP_VER}
    echo Instalado en: {target_dir}
    echo https://github.com/DarckRovert/Gravity_AI_bridge
    exit /b 0
)

if "%~1"=="--install" (
    python "{target_dir}\\INSTALAR.py"
    exit /b 0
)

if "%~1"=="--server" (
    start "" "{target_dir}\\INICIAR_SERVIDOR.bat"
    exit /b 0
)

if "%~1"=="--dashboard" (
    start "" "http://localhost:7860"
    exit /b 0
)

if "%~1"=="--status" (
    python "{target_dir}\\health_check.py"
    exit /b 0
)

if "%~1"=="--uninstall" (
    "{target_dir}\\DESINSTALAR.bat"
    exit /b 0
)

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python no encontrado. Descarga: https://www.python.org/downloads/
    exit /b 1
)

python -m pip install rich pyfiglet pyreadline3 -q --no-warn-script-location >nul 2>&1
python "{target_dir}\\ask_deepseek.py" %*
"""
    bat_path = os.path.join(target_dir, "gravity.bat")
    with open(bat_path, "w", encoding="utf-8") as f:
        f.write(content)


def _generate_desinstalar(target_dir: str):
    """Genera DESINSTALAR.bat en el directorio de instalación con rutas absolutas."""
    content = f"""@echo off
setlocal enabledelayedexpansion
cd /d "{target_dir}"
title DESINSTALADOR - GRAVITY AI BRIDGE V{APP_VER}
color 0c
cls

echo.
echo  +--------------------------------------------------------------+
echo  ^|         DESINSTALACION LIMPIA - GRAVITY AI BRIDGE V{APP_VER}       ^|
echo  +--------------------------------------------------------------+
echo.
echo  Directorio de instalacion: {target_dir}
echo.

REM ── [PASO 1/4] Limpiar PATH del usuario ──────────────────────────────────────
echo  [1/4] Removiendo 'gravity' del PATH del usuario...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$n = ([Environment]::GetEnvironmentVariable('Path','User') -split ';' | Where-Object {{ $_ -ne '{target_dir}' }}) -join ';'; [Environment]::SetEnvironmentVariable('Path',$n,'User'); Write-Host '   [OK] PATH restaurado.'"

REM ── [PASO 2/4] Eliminar acceso directo del Escritorio ────────────────────────
echo  [2/4] Eliminando icono del Escritorio...
powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$l = [Environment]::GetFolderPath('Desktop') + '\\Gravity AI Auditor.lnk'; if(Test-Path $l){{ Remove-Item $l -Force }}; Write-Host '   [OK] Listo.'"

REM ── [PASO 3/4] Eliminar configuraciones de IDEs ───────────────────────────────
echo  [3/4] Limpiando configuraciones de IDEs...
if exist "{target_dir}\\.continue\\config.yaml"    del /Q "{target_dir}\\.continue\\config.yaml"
if exist "{target_dir}\\aider.conf.yml"             del /Q "{target_dir}\\aider.conf.yml"
if exist "{target_dir}\\_integrations\\cursor.json" del /Q "{target_dir}\\_integrations\\cursor.json"
echo    [OK] IDEs limpiados.

REM ── [PASO 4/4] Resetear estado de primera ejecucion ──────────────────────────
echo  [4/4] Limpiando estado de primera ejecucion...
if exist "{target_dir}\\_first_run_done" del /Q "{target_dir}\\_first_run_done"
echo    [OK] Listo.

echo.
echo  +--------------------------------------------------------------+
echo  ^|                   DESINSTALACION COMPLETA                    ^|
echo  +--------------------------------------------------------------+
echo.
echo    El puente ha sido removido de tu PATH y Escritorio.
echo.
echo    Archivos CONSERVADOS en: {target_dir}
echo      - _knowledge.json    (base de conocimiento)
echo      - _audit_log.jsonl   (historial de auditorias)
echo      - _saves\\            (sesiones guardadas)
echo.
echo    Para eliminar completamente, borra la carpeta:
echo      {target_dir}
echo.
pause
exit /b 0
"""
    dst = os.path.join(target_dir, "DESINSTALAR.bat")
    with open(dst, "w", encoding="utf-8") as f:
        f.write(content)


def _register_path(target_dir: str, progress: Progress):
    """Registra target_dir en el PATH del usuario (persistente)."""
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Environment", 0, winreg.KEY_READ | winreg.KEY_WRITE
        )
        try:
            current, _ = winreg.QueryValueEx(key, "Path")
        except FileNotFoundError:
            current = ""

        paths = [p for p in current.split(";") if p.strip()]
        if target_dir not in paths:
            paths.append(target_dir)
            new_path = ";".join(paths)
            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
            # Notificar al sistema del cambio
            try:
                HWND_BROADCAST  = 0xFFFF
                WM_SETTINGCHANGE = 0x001A
                ctypes.windll.user32.SendMessageTimeoutW(
                    HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment", 2, 5000, None
                )
            except Exception:
                pass
        winreg.CloseKey(key)
    except Exception:
        pass


def _create_shortcut(target_dir: str):
    """Crea acceso directo en el Escritorio."""
    try:
        import winreg
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        # Buscar también en OneDrive Desktop
        try:
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders"
            )
            desktop, _ = winreg.QueryValueEx(key, "Desktop")
            winreg.CloseKey(key)
        except Exception:
            pass

        lnk_path = os.path.join(desktop, "Gravity AI Auditor.lnk")

        # Usar PowerShell para crear el .lnk (no requiere pywin32)
        script = f"""
$ws = New-Object -ComObject WScript.Shell
$s  = $ws.CreateShortcut('{lnk_path}')
$s.TargetPath    = 'cmd.exe'
$s.Arguments     = '/k "{target_dir}\\INICIAR_AUDITOR.bat"'
$s.WorkingDirectory = '{target_dir}'
$s.Description   = 'Gravity AI Bridge {APP_VER}'
$s.Save()
""".strip()
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script],
            capture_output=True, timeout=10
        )
    except Exception:
        pass


def _write_manifest(target_dir: str, source_dir: str, components: dict,
                    hw: dict, engines: dict, copied: int):
    """Escribe _install_manifest.json en el directorio de instalación."""
    manifest = {
        "version":       APP_VER,
        "install_path":  target_dir,
        "source_path":   source_dir,
        "installed_at":  datetime.now().isoformat(),
        "python_version": sys.version,
        "components":    {k: v for k, v in components.items() if v},
        "hardware": {
            "gpu":     hw.get("gpu_name"),
            "vram_mb": hw.get("vram_mb"),
            "ram_mb":  hw.get("total_ram_mb"),
            "gpu_type": hw.get("gpu_type"),
        },
        "engines_at_install": list(engines.keys()),
        "files_copied":  copied,
    }
    path = os.path.join(target_dir, "_install_manifest.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


# ══════════════════════════════════════════════════════════════════════════════
# RESUMEN FINAL
# ══════════════════════════════════════════════════════════════════════════════

def phase_summary(target_dir: str, hw: dict, engines: dict,
                  failed_pkgs: list, components: dict, copied: int):
    console.clear()
    console.print(Panel(
        Align.center(
            "[bold bright_green]✔ INSTALACIÓN COMPLETADA[/]\n"
            f"[dim]Gravity AI Bridge {APP_VER} instalado correctamente[/]"
        ),
        border_style="green",
        box=box.DOUBLE,
        padding=(1, 6),
    ))
    console.print()

    # Sistema
    sys_t = Table(title="[bold cyan]Sistema[/]", box=box.SIMPLE_HEAD, padding=(0, 2))
    sys_t.add_column("", style="dim",  width=20)
    sys_t.add_column("", style="white")
    sys_t.add_row("Instalado en",  f"[bold]{target_dir}[/]")
    sys_t.add_row("GPU",    hw.get("gpu_name", "N/A"))
    sys_t.add_row("VRAM",   f"{hw.get('vram_mb', 0):,} MB")
    sys_t.add_row("RAM",    f"{hw.get('total_ram_mb', 0):,} MB")
    sys_t.add_row("Python", sys.version.split()[0])
    if engines:
        sys_t.add_row("Motores", ", ".join(engines.keys()))
    else:
        sys_t.add_row("Motores", "[yellow]Ninguno detectado[/]")
    if copied > 0:
        sys_t.add_row("Archivos copiados", str(copied))
    console.print(sys_t)
    console.print()

    if failed_pkgs:
        console.print(f"[yellow]⚠ Paquetes no instalados: {', '.join(failed_pkgs)}[/]")
        console.print("[dim]  Instálalos manualmente con: pip install <paquete>[/]")
        console.print()

    # Instrucciones de uso
    use_t = Table(title="[bold cyan]Cómo usar[/]", box=box.SIMPLE_HEAD, padding=(0, 2))
    use_t.add_column("Acción", style="cyan",  width=30)
    use_t.add_column("Comando / Ruta")
    use_t.add_row("CLI interactivo",      "[bold]gravity[/]  [dim](nueva terminal)[/]")
    use_t.add_row("Bridge server",        "[bold]gravity --server[/]")
    use_t.add_row("Dashboard web",        "[cyan]http://localhost:7860[/]")
    use_t.add_row("API endpoint",         "[cyan]http://localhost:7860/v1[/]")
    use_t.add_row("Acceso directo",       "Escritorio → Gravity AI Auditor")
    use_t.add_row("Desinstalar",          "[bold]gravity --uninstall[/]")
    console.print(use_t)
    console.print()

    console.print(
        "[dim]Documentación completa: [/]"
        "[cyan]github.com/DarckRovert/Gravity_AI_bridge[/]  ·  "
        "[dim]Stream:[/] [cyan]twitch.tv/darckrovert[/]"
    )
    console.print()

    if Confirm.ask("¿Abrir el dashboard web ahora?", default=False):
        server_bat = os.path.join(target_dir, "INICIAR_SERVIDOR.bat")
        if os.path.exists(server_bat):
            subprocess.Popen(["cmd", "/c", server_bat], creationflags=0x00000010)
            time.sleep(2)
            import webbrowser
            webbrowser.open("http://localhost:7860")


# ══════════════════════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════

def main():
    # Parseo de argumentos mínimo (sin argparse para no añadir dependencia)
    args = sys.argv[1:]
    cli_dir   = None
    in_place  = False

    i = 0
    while i < len(args):
        if args[i] == "--dir" and i + 1 < len(args):
            cli_dir = args[i + 1]
            i += 2
        elif args[i] == "--in-place":
            in_place = True
            i += 1
        else:
            i += 1

    # ── Fase 1: Bienvenida ─────────────────────────────────────────────────────
    phase_welcome()

    if not Confirm.ask(
        "[bold cyan]¿Iniciar la instalación de Gravity AI Bridge?[/]",
        default=True
    ):
        console.print("[dim]Instalación cancelada.[/]")
        sys.exit(0)

    console.print()

    # ── Fase 2: Directorio de instalación ─────────────────────────────────────
    target_dir = phase_choose_directory(cli_dir=cli_dir, in_place=in_place)

    # ── Fase 3: Componentes ────────────────────────────────────────────────────
    console.print()
    components = phase_components()

    # ── Verificar Python >= 3.10 ───────────────────────────────────────────────
    if sys.version_info < (3, 10):
        console.print(f"[red]✖ Python 3.10+ requerido. Versión actual: {sys.version.split()[0]}[/]")
        console.print("[yellow]  Descarga: https://www.python.org/downloads/[/]")
        sys.exit(1)

    # ── Fases 4-10: Ejecución con barra de progreso ────────────────────────────
    hw      = {}
    engines = {}
    copied  = 0
    failed  = []

    with Progress(
        SpinnerColumn(),
        BarColumn(bar_width=32),
        TextColumn("[progress.description]{task.description}"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:

        # [1] Detección de hardware
        t1 = progress.add_task("[cyan]Detectando hardware...", total=1)
        hw = _detect_hardware()
        progress.advance(t1)

        # [2] Detección de motores locales
        t2 = progress.add_task("[cyan]Detectando motores de IA locales...", total=1)
        engines = _detect_local_engines()
        progress.advance(t2)

        # [3] Copia de archivos (solo si instalación en directorio diferente)
        if os.path.abspath(target_dir) != os.path.abspath(SOURCE_DIR):
            copied = phase_copy_files(target_dir, progress)
        else:
            t_skip = progress.add_task("[dim]Instalación in-place (sin copia)...", total=1)
            progress.advance(t_skip)
            copied = 0

        # [4] Instalación de dependencias Python
        failed = phase_install_deps(components, progress)

        # [5] Generar config.yaml
        t5 = progress.add_task("[cyan]Generando config.yaml...", total=1)
        _generate_config(target_dir, hw, engines)
        progress.advance(t5)

        # [6] Generar gravity.bat con rutas absolutas al destino
        t6 = progress.add_task("[cyan]Generando gravity.bat...", total=1)
        _generate_gravity_bat(target_dir)
        progress.advance(t6)

        # [7] Generar DESINSTALAR.bat con rutas absolutas al destino
        t7 = progress.add_task("[cyan]Generando DESINSTALAR.bat...", total=1)
        _generate_desinstalar(target_dir)
        progress.advance(t7)

        # [8] Registrar PATH
        t8 = progress.add_task("[cyan]Registrando en PATH del usuario...", total=1)
        _register_path(target_dir, progress)
        progress.advance(t8)

        # [9] Crear acceso directo en Escritorio
        t9 = progress.add_task("[cyan]Creando acceso directo en Escritorio...", total=1)
        _create_shortcut(target_dir)
        progress.advance(t9)

        # [10] Escribir manifest de instalación
        t10 = progress.add_task("[cyan]Escribiendo manifiesto de instalación...", total=1)
        _write_manifest(target_dir, SOURCE_DIR, components, hw, engines, copied)
        progress.advance(t10)

    # ── Fase final: Resumen ────────────────────────────────────────────────────
    phase_summary(target_dir, hw, engines, failed, components, copied)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[dim]Instalación interrumpida por el usuario.[/]")
        sys.exit(0)
    except Exception as e:
        import traceback
        console.print(f"\n[red]Error fatal en el instalador:[/] {e}")
        console.print(f"[dim]{traceback.format_exc()}[/]")
        sys.exit(1)
