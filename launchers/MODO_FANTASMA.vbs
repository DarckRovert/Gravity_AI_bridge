Set objFSO = CreateObject("Scripting.FileSystemObject")
strLaunchers = objFSO.GetParentFolderName(WScript.ScriptFullName)
strRoot = objFSO.GetParentFolderName(strLaunchers)
Set WshShell = CreateObject("WScript.Shell")

' Enrutamiento forzoso a la raiz para acceso a modulos base
WshShell.CurrentDirectory = strRoot

' Inyectar timestamp en el log antes de arrancar
Dim strDate : strDate = Now()
Dim strLog  : strLog  = strRoot & "\bridge.log"
Dim ts : Set ts = objFSO.OpenTextFile(strLog, 8, True)  ' 8 = append, True = create
ts.WriteLine ""
ts.WriteLine "========== MODO FANTASMA ARRANQUE: " & strDate & " =========="
ts.Close

' Ejecucion silenciosa (0 = Oculto, False = No suspender script)
' Captura de STDOUT/STDERR en el nivel del bridge (append, no sobrescribir)
WshShell.Run "cmd /c ""python bridge_server.py >> bridge.log 2>&1""", 0, False

MsgBox "Gravity Bridge Server V16.0 PRO iniciado en modo fantasma." & vbCrLf & "Logs en: " & strLog, 64, "Gravity AI"
