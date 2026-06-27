[Setup]
AppName=Gravity AI Bridge PRO
AppVersion=16.4
DefaultDirName={pf}\Gravity AI Bridge
DefaultGroupName=Gravity AI
UninstallDisplayIcon={app}\Gravity AI Launcher.exe
Compression=lzma2
SolidCompression=yes
OutputDir=dist
OutputBaseFilename=GravityAI_Bridge_Installer_16.4

[Files]
Source: "dist\Gravity AI Launcher\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Gravity AI"; Filename: "{app}\Gravity AI Launcher.exe"
Name: "{commondesktop}\Gravity AI"; Filename: "{app}\Gravity AI Launcher.exe"

[Run]
Filename: "{app}\Gravity AI Launcher.exe"; Description: "Launch Gravity AI Bridge"; Flags: nowait postinstall skipifsilent
