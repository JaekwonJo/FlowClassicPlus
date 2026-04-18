@echo off
cd /d "%~dp0"
start "" wscript.exe //nologo "%~dp0story_prompt_pipeline_run.vbs"
exit /b
