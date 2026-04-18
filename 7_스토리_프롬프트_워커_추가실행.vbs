Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

basePath = fso.GetParentFolderName(WScript.ScriptFullName)
localPyw = WshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\FlowClassicPlus\runtime\python-embed\pythonw.exe"
legacyLocalPyw = WshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Autoupload\runtime\python-embed\pythonw.exe"
legacyPyw = basePath & "\runtime\python-embed\pythonw.exe"

workerName = "story_worker2"
If WScript.Arguments.Count > 0 Then
    workerName = Trim(CStr(WScript.Arguments(0)))
    If workerName = "" Then
        workerName = "story_worker2"
    End If
End If

WshShell.CurrentDirectory = basePath

checkSystem = WshShell.Run("cmd /c python -c ""import tkinter""", 0, True)

If checkSystem = 0 Then
    WshShell.Run "pythonw story_prompt_pipeline.py --instance-name """ & workerName & """", 0
ElseIf fso.FileExists(localPyw) Then
    WshShell.Run """" & localPyw & """ story_prompt_pipeline.py --instance-name """ & workerName & """", 0
ElseIf fso.FileExists(legacyLocalPyw) Then
    WshShell.Run """" & legacyLocalPyw & """ story_prompt_pipeline.py --instance-name """ & workerName & """", 0
ElseIf fso.FileExists(legacyPyw) Then
    WshShell.Run """" & legacyPyw & """ story_prompt_pipeline.py --instance-name """ & workerName & """", 0
Else
    MsgBox "pythonw not found for story prompt pipeline.", vbExclamation, "Story Prompt Pipeline"
End If

Set fso = Nothing
Set WshShell = Nothing
