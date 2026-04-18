@echo off
cd /d "%~dp0"
set /p STORY_WORKER_NAME=새 스토리 워커 이름을 입력하세요 (예: story_worker2): 
if "%STORY_WORKER_NAME%"=="" set STORY_WORKER_NAME=story_worker2
start "" wscript.exe //nologo "%~dp0story_prompt_pipeline_worker_run.vbs" "%STORY_WORKER_NAME%"
exit /b
