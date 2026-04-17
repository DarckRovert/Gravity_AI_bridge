; â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
; GRAVITY AI BRIDGE V10.0 â€” Inno Setup Script
; Compilar con: Inno Setup Compiler 6.x (https://jrsoftware.org/isinfo.php)
; â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

#define AppName    "Gravity AI Bridge"
#define AppVersion "10.0"
#define AppPublisher "DarckRovert"
#define AppURL     "https://github.com/DarckRovert/Gravity_AI_bridge"
#define AppExe     "GravityBridge.exe"
#define AppIcon    "..\assets\gravity_icon.ico"

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
; Windows 10 1809+ mÃ­nimo
DisableProgramGroupPage=yes
UninstallDisplayIcon={app}\{#AppExe}
UninstallDisplayName={#AppName} V{#AppVersion}
VersionInfoVersion={#AppVersion}
VersionInfoCompany={#AppPublisher}
VersionInfoDescription={#AppName} â€” Orquestador de IA Local de Alto Rendimiento
VersionInfoCopyright=Copyright (C) 2026 {#AppPublisher}. Strictly Non-Commercial.

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon";      Description: "Crear icono en el Escritorio";         GroupDescription: "Accesos Directos:"
Name: "startmenufolder"; Description: "Crear carpeta en el Menú de Inicio";   GroupDescription: "Accesos Directos:"
Name: "autostart";        Description: "Iniciar Gravity AI Bridge con Windows"; GroupDescription: "Opciones:"

[Files]
; Ejecutable principal (generado por PyInstaller)
Source: "..\dist\GravityBridge.exe";     DestDir: "{app}";             Flags: ignoreversion

; Assets web del Dashboard (hot-reload desde disco)
Source: "..\web\*";                      DestDir: "{app}\web";         Flags: ignoreversion recursesubdirs createallsubdirs

; ConfiguraciÃ³n inicial
Source: "..\config.yaml";               DestDir: "{app}";             Flags: ignoreversion onlyifdoesntexist
Source: "..\_knowledge.json";           DestDir: "{app}";             Flags: ignoreversion onlyifdoesntexist

; Icono
Source: "..\assets\gravity_icon.ico";   DestDir: "{app}\assets";      Flags: ignoreversion

; Wiki & DocumentaciÃ³n
Source: "..\wiki\*";                     DestDir: "{app}\wiki";        Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\README.md";                  DestDir: "{app}";             Flags: ignoreversion

[Icons]
Name: "{group}\{#AppName}";                   Filename: "{app}\{#AppExe}"; IconFilename: "{app}\assets\gravity_icon.ico"
Name: "{group}\Desinstalar {#AppName}";       Filename: "{uninstallexe}"
Name: "{commondesktop}\{#AppName}";            Filename: "{app}\{#AppExe}"; IconFilename: "{app}\assets\gravity_icon.ico"; Tasks: desktopicon
Name: "{userstartup}\{#AppName}";             Filename: "{app}\{#AppExe}"; IconFilename: "{app}\assets\gravity_icon.ico"; Tasks: autostart

[Registry]
; Autostart opcional
Root: HKCU; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; ValueType: string; ValueName: "GravityAIBridge"; ValueData: """{app}\{#AppExe}"""; Flags: uninsdeletevalue; Tasks: autostart

[Run]
Filename: "{app}\{#AppExe}"; Description: "Iniciar Gravity AI Bridge ahora"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "taskkill.exe"; Parameters: "/F /IM {#AppExe}"; Flags: runhidden

[UninstallDelete]
Type: files;     Name: "{app}\_gravity_launcher.pid"
Type: files;     Name: "{app}\_settings.json"
Type: filesandordirs; Name: "{app}\__pycache__"

[Code]
procedure InitializeWizard;
begin
  WizardForm.WelcomeLabel2.Caption :=
    'Este asistente instalarÃ¡ Gravity AI Bridge V10.0 en tu computadora.' + #13#10 + #13#10 +
    'Gravity AI Bridge es un orquestador de IA local que te permite usar modelos' + #13#10 +
    'de lenguaje (LLMs) de forma eficiente, privada y sin dependencia de la nube.' + #13#10 + #13#10 +
    'Compatible con LM Studio, Ollama, Kobold, Jan y mÃ¡s.' + #13#10 + #13#10 +
    'Haz clic en Siguiente para continuar.';
end;
