Param(
  [string[]]$ExtraTokens
)

Write-Host "[stop] Enumerating Telegram-related processes..."

# 1) Stop Python/Node processes that look like our bots
$procs = Get-CimInstance Win32_Process | Where-Object {
  $_.Name -match '^(python|pythonw|node)\.exe$' -and (
    $_.CommandLine -match 'main_enhanced\.py|main_webhook\.py|run\.py|telegram|bot'
  )
}
foreach ($p in $procs) {
  try {
    Write-Host ("[stop] PID={0} Name={1} Cmd={2}" -f $p.ProcessId, $p.Name, $p.CommandLine)
    Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
  } catch {}
}

# 2) Remove local lock file if exists
$lockPath = Join-Path $PSScriptRoot "..\automation_hub.lock"
if (Test-Path $lockPath) {
  try {
    $meta = Get-Content $lockPath -Raw | ConvertFrom-Json
    if ($meta.pid) {
      Write-Host "[stop] Killing lock PID $($meta.pid)"
      Stop-Process -Id $meta.pid -Force -ErrorAction SilentlyContinue
    }
  } catch {}
  try { Remove-Item $lockPath -Force } catch {}
}

# 3) Delete webhook and drop pending updates for known tokens
function Get-TokensFromEnv($path) {
  $tokens = @()
  if (Test-Path $path) {
    $lines = Get-Content $path -Encoding UTF8
    foreach ($line in $lines) {
      if ($line -match '^(TELEGRAM_TOKEN|TELEGRAM_BOT_TOKEN[\w_]*)=(.+)$') {
        $tokens += $Matches[2].Trim()
      }
    }
  }
  return $tokens
}

$repoRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$envFile = Join-Path $repoRoot ".env"
$tokens = @()
$tokens += Get-TokensFromEnv $envFile
if ($ExtraTokens) { $tokens += $ExtraTokens }

if ($tokens.Count -gt 0) {
  Write-Host "[stop] Clearing webhooks for $($tokens.Count) token(s)"
  foreach ($t in $tokens | Select-Object -Unique) {
    try {
      $url = "https://api.telegram.org/bot$($t)/deleteWebhook?drop_pending_updates=true"
      Write-Host "[stop] DELETE webhook -> $url"
      Invoke-WebRequest -UseBasicParsing -Uri $url -Method Post -TimeoutSec 15 | Out-Null
    } catch {
      Write-Host "[stop] Failed to delete webhook for token (masked): ***$(($t.Substring(0,8)))..."
    }
  }
} else {
  Write-Host "[stop] No tokens found in .env. Skipped webhook cleanup."
}

Write-Host "[stop] Done."

