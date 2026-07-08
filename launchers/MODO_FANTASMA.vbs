Set objFSO = CreateObject("Scripting.FileSystemObject")
strLaunchers = objFSO.GetParentFolderName(WScript.ScriptFullName)
strRoot = objFSO.GetParentFolderName(strLaunchers)
Set WshShell = CreateObject("WScript.Shell")

' Enrutamiento forzoso a la raiz para acceso a modulos base
WshShell.CurrentDirectory = strRoot

' Inyectar timestamp en el log antes de arrancar
Dim strDate : strDate = Now()
' Obtener ruta de AppData para el log
Set objShell = CreateObject("WScript.Shell")
strAppData = objShell.ExpandEnvironmentStrings("%LOCALAPPDATA%")
strLogFolder = strAppData & "\Gravity\Logs"

' Crear carpeta si no existe
If Not objFSO.FolderExists(strLogFolder) Then
    BuildFullPath(strLogFolder)
End If

Dim strLog : strLog = strLogFolder & "\bridge.log"

Dim ts : Set ts = objFSO.OpenTextFile(strLog, 8, True)  ' 8 = append, True = create
ts.WriteLine ""
ts.WriteLine "========== MODO FANTASMA ARRANQUE: " & strDate & " =========="
ts.Close

' Ejecucion silenciosa (0 = Oculto, False = No suspender script)
' Captura de STDOUT/STDERR en el nivel del bridge (append, no sobrescribir)
WshShell.Run "cmd /c ""python bridge_server.py >> """ & strLog & """ 2>&1""", 0, False

MsgBox "Gravity Bridge Server V16.14 PRO iniciado en modo fantasma." & vbCrLf & "Logs en: " & strLog, 64, "Gravity AI"

' Funcion para crear carpetas recursivamente
Sub BuildFullPath(ByVal strPath)
    If Not objFSO.FolderExists(objFSO.GetParentFolderName(strPath)) Then
        BuildFullPath objFSO.GetParentFolderName(strPath)
    End If
    objFSO.CreateFolder strPath
End Sub
