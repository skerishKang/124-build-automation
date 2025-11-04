Write-Host "[setup] Installing Python dependencies..."
try {
  pip install -r ..\requirements.txt
} catch {
  Write-Host "[setup] pip install failed. Ensure Python/pip is in PATH." -ForegroundColor Red
  exit 1
}

Write-Host "[setup] Checking ffmpeg..."
try {
  & ffmpeg -version | Out-Null
  Write-Host "[setup] ffmpeg OK"
} catch {
  Write-Host "[setup] ffmpeg missing. Install and add to PATH: https://ffmpeg.org/download.html" -ForegroundColor Yellow
}

Write-Host "[setup] Verifying anthropic & faster-whisper..."
pip show anthropic | Out-Null
if (!$?) { Write-Host "[setup] anthropic not installed (will install via requirements)." }
pip show faster-whisper | Out-Null
if (!$?) { Write-Host "[setup] faster-whisper not installed (will install via requirements)." }

Write-Host "[setup] Stopping any residual bots..."
powershell -ExecutionPolicy Bypass -File .\stop_telegram_bots.ps1

Write-Host "[run] Starting bot (run.py)...\n"
cd ..
python run.py
