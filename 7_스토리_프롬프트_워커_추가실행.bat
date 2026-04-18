@echo off
cd /d "%~dp0"
set /p STORY_WORKER_NAME=새 스토리 워커 이름을 입력하세요 (예: story_worker2): 
if "%STORY_WORKER_NAME%"=="" set STORY_WORKER_NAME=story_worker2
python story_prompt_pipeline.py --instance-name "%STORY_WORKER_NAME%"
pause
