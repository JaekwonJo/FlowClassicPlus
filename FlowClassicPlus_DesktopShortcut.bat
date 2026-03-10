@echo off
setlocal
cd /d "%~dp0"

set "ICON=%CD%\icon.ico"
set "VBS=%CD%\Flow_Start.vbs"

echo [INFO] Creating desktop shortcut: Flow Classic Plus.lnk
powershell -NoProfile -ExecutionPolicy Bypass -Command "$ErrorActionPreference='Stop';$ws=New-Object -ComObject WScript.Shell;$desk=[Environment]::GetFolderPath('Desktop');$lnk=$ws.CreateShortcut((Join-Path $desk 'Flow Classic Plus.lnk'));$lnk.TargetPath=(Join-Path $env:WINDIR 'System32\wscript.exe');$lnk.Arguments='""%VBS%""';$lnk.WorkingDirectory='%CD%';if(Test-Path '%ICON%'){$lnk.IconLocation='%ICON%'};$lnk.Description='Flow Classic Plus launcher';$lnk.Save()"

if errorlevel 1 (
  echo [ERROR] Failed to create desktop shortcut.
) else (
  echo [OK] Desktop shortcut created: Flow Classic Plus.lnk
)

echo.
pause
