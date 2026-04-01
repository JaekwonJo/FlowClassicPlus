@echo off
chcp 65001 >nul
cd /d %~dp0

echo ========================================================
echo [Flow Classic Plus] 긴급 수리: pynput 설치
echo ========================================================
echo.
echo Installing 'pynput' to allow detecting 'Enter' key
echo for coordinate capture mode.
echo.

set "PYCMD=python"
where py >nul 2>&1 && set "PYCMD=py -3"

echo Using Python: %PYCMD%
echo.

%PYCMD% -m pip install --upgrade pip
%PYCMD% -m pip install pyautogui pyperclip opencv-python pillow pynput pystray

echo.
echo ========================================================
echo [OK] Ready to capture coordinates with Enter key!
echo Run '2_오토_프로그램_실행.bat' now.
echo ========================================================
pause
