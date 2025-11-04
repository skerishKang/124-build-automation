@echo off
setlocal
call .venv\Scripts\activate
set BOT_MODE=polling
set LOG_FILE=logs/automation_hub.log
set LLM_PROVIDER=gemini
set GEMINI_MODEL=gemini-2.5-flash
python run.py
