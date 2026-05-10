Set objFSO = CreateObject("Scripting.FileSystemObject")
strLaunchers = objFSO.GetParentFolderName(WScript.ScriptFullName)
strRoot = objFSO.GetParentFolderName(strLaunchers)
Set WshShell = CreateObject("WScript.Shell")

' Enrutamiento forzoso a la raiz para acceso a modulos base
WshShell.CurrentDirectory = strRoot

' Ejecucion silenciosa (0 = Oculto, False = No suspender script) 
' Captura de STDOUT/STDERR en el nivel del bridge
WshShell.Run "cmd /c ""python bridge_server.py > bridge.log 2>&1""", 0, False

MsgBox "Gravity Bridge Server V13.0 PRO iniciado en modo fantasma. Logs en bridge.log", 64, "Gravity AI"
