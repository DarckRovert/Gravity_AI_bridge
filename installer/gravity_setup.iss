; ══════════════════════════════════════════════════════════════════════════════
; GRAVITY AI BRIDGE V16.0 PRO — Inno Setup Script
; Compilar con: Inno Setup Compiler 6.x (https://jrsoftware.org/isinfo.php)
; ══════════════════════════════════════════════════════════════════════════════

#define AppName      "Gravity AI Bridge"
#define AppVersion   "15.1"
#define AppPublisher "DarckRovert"
#define AppURL       "https://github.com/DarckRovert/Gravity_AI_bridge"
#define AppExe       "GravityBridge.exe"
#define AppIcon      "..\assets\gravity_icon.ico"

[Setup]
AppId={{8A3F9B2C-4D71-4E8A-B9C3-D5F6A7E8B901}
AppName={#AppName}
AppVersion={#AppVersion}
AppPublisherURL={#AppURL}
AppSupportURL={#AppURL}/issues
AppUpdatesURL={#AppURL}/releases
DefaultDirName={autopf}\{#AppName}
DefaultGroupName={#AppName}
OutputDir=..\dist
OutputBaseFilename=Gravity_AI_Bridge_V{#AppVersion}_Setup
SetupIconFile={#AppIcon}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64
MinVersion=10.0.17763
; Windows 10 1809+ mínimo
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName} V{#AppVersion}
VersionInfoVersion={#AppVersion}.0
VersionInfoCompany={#AppPublisher}
VersionInfoDescription={#AppName} — Orquestador de IA Local Omniscient-Tier V16.0 PRO
VersionInfoCopyright=Copyright (C) 2026 {#AppPublisher}. Strictly Non-Commercial.
; Diálogo de bienvenida con imagen personalizada (si existe)
; WizardImageFile=..\assets\setup_banner.bmp

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";      Description: "Crear icono en el Escritorio";           GroupDescription: "Accesos Directos:"
Name: "startmenufolder";  Description: "Crear carpeta en el Menú de Inicio";     GroupDescription: "Accesos Directos:"
Name: "autostart";        Description: "Iniciar Gravity AI Bridge con Windows";  GroupDescription: "Opciones de Inicio:"
Name: "tray";             Description: "Ejecutar minimizado en la bandeja del sistema"; GroupDescription: "Opciones de Inicio:"

[Files]
; ── Ejecutable principal (generado por PyInstaller) ─────────────────────────
Source: "..\dist\GravityBridge.exe";          DestDir: "{app}";               Flags: ignoreversion

; ── Frontend compilado (build de producción React) ──────────────────────────
Source: "..\frontend\dist\*";                 DestDir: "{app}\web";           Flags: ignoreversion recursesubdirs createallsubdirs

; ── Configuración inicial (no sobreescribir si ya existe) ────────────────────
Source: "..\config.yaml.example";                     DestDir: "{app}"; DestName: "config.yaml"; Flags: ignoreversion onlyifdoesntexist
Source: "..\_knowledge.json";                 DestDir: "{app}";               Flags: ignoreversion onlyifdoesntexist

; ── Assets (icono, etc.) ─────────────────────────────────────────────────────
Source: "..\assets\gravity_icon.ico";         DestDir: "{app}\assets";        Flags: ignoreversion

; ── Wiki y Documentación ─────────────────────────────────────────────────────
Source: "..\wiki\*";                          DestDir: "{app}\wiki";          Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\README.md";                       DestDir: "{app}";               Flags: ignoreversion
Source: "..\CHANGELOG.md";                    DestDir: "{app}";               Flags: ignoreversion
Source: "..\SECURITY.md";                     DestDir: "{app}";               Flags: ignoreversion
Source: "..\LICENSE";                         DestDir: "{app}";               Flags: ignoreversion

[Icons]
; Menú de inicio
Name: "{group}\{#AppName}";                         Filename: "{app}\{#AppExe}"; IconFilename: "{app}\assets\gravity_icon.ico"
Name: "{group}\Dashboard (Navegador)";              Filename: "{app}\{#AppExe}"; Parameters: "--open-dashboard"; IconFilename: "{app}\assets\gravity_icon.ico"
Name: "{group}\Desinstalar {#AppName}";             Filename: "{uninstallexe}"

; Escritorio
Name: "{commondesktop}\{#AppName}";                 Filename: "{app}\{#AppExe}"; IconFilename: "{app}\assets\gravity_icon.ico"; Tasks: desktopicon

; Inicio automático con Windows
Name: "{userstartup}\{#AppName}";                   Filename: "{app}\{#AppExe}"; IconFilename: "{app}\assets\gravity_icon.ico"; Tasks: autostart

[Registry]
; Autostart opcional (inicio con Windows)
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
  ValueType: string; ValueName: "GravityAIBridge"; \
  ValueData: """{app}\{#AppExe}"""; \
  Flags: uninsdeletevalue; Tasks: autostart

; Registro de la aplicación para Control Panel → Programas
Root: HKLM; Subkey: "Software\DarckRovert\{#AppName}"; \
  ValueType: string; ValueName: "InstallPath"; \
  ValueData: "{app}"; Flags: uninsdeletekey

[Run]
; Abrir el Dashboard en el navegador tras instalar
Filename: "{app}\{#AppExe}"; Description: "Iniciar Gravity AI Bridge ahora"; \
  Flags: nowait postinstall skipifsilent; WorkingDir: "{app}"

[UninstallRun]
; Matar el proceso antes de desinstalar
Filename: "taskkill.exe"; Parameters: "/F /IM {#AppExe}"; Flags: runhidden; RunOnceId: "KillGravity"

[UninstallDelete]
; Eliminar archivos runtime generados en {app} (no en AppData)
Type: files;          Name: "{app}\_gravity_launcher.pid"
Type: files;          Name: "{app}\_settings.json"
Type: files;          Name: "{app}\_first_run_done"
Type: files;          Name: "{app}\bridge.log"
Type: files;          Name: "{app}\_audit_log.jsonl"
Type: files;          Name: "{app}\_cost_log.json"
Type: filesandordirs; Name: "{app}\__pycache__"
Type: filesandordirs; Name: "{app}\_cache.sqlite"
Type: filesandordirs; Name: "{app}\_image_queue.sqlite"
Type: filesandordirs; Name: "{app}\_video_queue.sqlite"

[Code]
procedure InitializeWizard;
begin
  WizardForm.WelcomeLabel2.Caption :=
    'Este asistente instalará Gravity AI Bridge V16.0 PRO en tu computadora.' + #13#10 + #13#10 +
    'Gravity AI Bridge es un orquestador de IA local Omniscient-Tier que permite gestionar' + #13#10 +
    'múltiples modelos de lenguaje (LLMs), pipelines multimedia, Game Servers y agentes' + #13#10 +
    'IA con intercepción HITL — todo desde un único Dashboard web.' + #13#10 + #13#10 +
    'Compatible con: LM Studio, Ollama, Kobold, Jan, OpenAI, Anthropic.' + #13#10 +
    'Firecrawl, MCP Servers, Video Studio, Image Lab y más.' + #13#10 + #13#10 +
    'Requiere Windows 10 1809+ de 64 bits.' + #13#10 + #13#10 +
    'Haz clic en Siguiente para continuar.';
end;

function InitializeUninstall(): Boolean;
var
  Ret: Integer;
begin
  // Matar el proceso si está corriendo antes de desinstalar
  Exec('taskkill.exe', '/F /IM GravityBridge.exe', '', SW_HIDE, ewWaitUntilTerminated, Ret);
  Result := True;
end;
