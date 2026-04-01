Set WshShell = CreateObject("WScript.Shell")
Set fso = CreateObject("Scripting.FileSystemObject")

basePath = fso.GetParentFolderName(WScript.ScriptFullName)
localPyw = WshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\FlowClassicPlus\runtime\python-embed\pythonw.exe"
legacyLocalPyw = WshShell.ExpandEnvironmentStrings("%LOCALAPPDATA%") & "\Autoupload\runtime\python-embed\pythonw.exe"
legacyPyw = basePath & "\runtime\python-embed\pythonw.exe"
fallbackBat = basePath & "\0_원터치_설치+실행.bat"

WshShell.CurrentDirectory = basePath

checkSystem = WshShell.Run("cmd /c python -c ""import tkinter,playwright,pystray,PIL""", 0, True)

If checkSystem = 0 Then
    WshShell.Run "pythonw -m flow.flow_auto_v2", 0
ElseIf fso.FileExists(localPyw) Then
    WshShell.Run """" & localPyw & """ -m flow.flow_auto_v2", 0
ElseIf fso.FileExists(legacyLocalPyw) Then
    WshShell.Run """" & legacyLocalPyw & """ -m flow.flow_auto_v2", 0
ElseIf fso.FileExists(legacyPyw) Then
    WshShell.Run """" & legacyPyw & """ -m flow.flow_auto_v2", 0
ElseIf fso.FileExists(fallbackBat) Then
    WshShell.Run """" & fallbackBat & """", 1
Else
    MsgBox "실행 파일을 찾지 못했습니다." & vbCrLf & _
           "0_원터치_설치+실행.bat을 먼저 실행해주세요.", vbExclamation, "Flow Classic Plus"
End If

Set fso = Nothing
Set WshShell = Nothing
