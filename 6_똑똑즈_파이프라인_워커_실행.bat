@echo off
cd /d "%~dp0"
start "" wscript.exe //nologo "%~dp0ttz_pipeline_worker_run.vbs"
exit /b
