@echo off
setlocal
cd /d "%~dp0"

if exist "FlowClassicPlus_DesktopShortcut.bat" (
  call "FlowClassicPlus_DesktopShortcut.bat"
) else (
  echo [ERROR] Missing file: FlowClassicPlus_DesktopShortcut.bat
  echo.
  pause
)
