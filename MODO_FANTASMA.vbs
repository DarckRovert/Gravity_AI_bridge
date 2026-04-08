Set objFSO = CreateObject("Scripting.FileSystemObject")
strFolder = objFSO.GetParentFolderName(WScript.ScriptFullName)
Set WshShell = CreateObject("WScript.Shell")

' Ejecuta el servidor usando python sin abrir ventana (0 = Oculto, False = No esperar a que termine)
' Toda la salida y los logs de las intercepciones de VS Code quedaran en bridge.log
WshShell.Run "cmd /c ""python """ & strFolder & "\bridge_server.py"" > """ & strFolder & "\bridge.log"" 2>&1""", 0, False

MsgBox "Gravity Bridge Server V8.0 Pro iniciado en modo fantasma. Logs en bridge.log", 64, "Gravity AI"
