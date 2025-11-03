@echo off
setlocal
call .venv\Scripts\activate
set BOT_MODE=polling
python run.py
