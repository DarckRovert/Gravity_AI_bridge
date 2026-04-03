Set oWS = WScript.CreateObject("WScript.Shell")
sLinkFile = oWS.SpecialFolders("Desktop") & "\Gravity AI Auditor.lnk"
Set oLink = oWS.CreateShortcut(sLinkFile)
oLink.TargetPath = WScript.Arguments(0) & "\INICIAR_AUDITOR.bat"
oLink.WorkingDirectory = WScript.Arguments(0)
oLink.IconLocation = "%SystemRoot%\System32\SHELL32.dll, 300"
oLink.Save
