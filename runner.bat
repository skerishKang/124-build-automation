@echo off
setlocal
call .venv\Scripts\activate
set BOT_MODE=polling
set LOG_FILE=logs/automation_hub.log
python run.py
