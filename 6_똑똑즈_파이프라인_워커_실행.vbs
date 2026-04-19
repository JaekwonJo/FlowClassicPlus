Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

basePath = fso.GetParentFolderName(WScript.ScriptFullName)
localPyw = WshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\FlowClassicPlus\runtime\python-embed\pythonw.exe"
legacyLocalPyw = WshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Autoupload\runtime\python-embed\pythonw.exe"
legacyPyw = basePath & "\runtime\python-embed\pythonw.exe"

WshShell.CurrentDirectory = basePath

checkSystem = WshShell.Run("cmd /c python -c ""import tkinter""", 0, True)

If checkSystem = 0 Then
    WshShell.Run "pythonw ttz_pipeline_worker.py --instance-name story_worker1", 0
ElseIf fso.FileExists(localPyw) Then
    WshShell.Run """" & localPyw & """ ttz_pipeline_worker.py --instance-name story_worker1", 0
ElseIf fso.FileExists(legacyLocalPyw) Then
    WshShell.Run """" & legacyLocalPyw & """ ttz_pipeline_worker.py --instance-name story_worker1", 0
ElseIf fso.FileExists(legacyPyw) Then
    WshShell.Run """" & legacyPyw & """ ttz_pipeline_worker.py --instance-name story_worker1", 0
Else
    MsgBox "pythonw not found for TTZ pipeline worker.", vbExclamation, "TTZ Pipeline Worker"
End If

Set fso = Nothing
Set WshShell = Nothing
