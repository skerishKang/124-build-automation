Param(
  [string]$EnvPath = ".env"
)

function Read-Secret($prompt) {
  $s = Read-Host -AsSecureString -Prompt $prompt
  $bstr = [System.Runtime.InteropServices.Marshal]::SecureStringToBSTR($s)
  try { return [System.Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr) }
  finally { [System.Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr) }
}

function Set-EnvVar($Path, $Key, $Value) {
  if ([string]::IsNullOrEmpty($Value)) { return }
  if (-not (Test-Path $Path)) { New-Item -ItemType File -Path $Path -Force | Out-Null }
  $lines = Get-Content $Path -Encoding UTF8
  $updated = $false
  for ($i=0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match "^$Key=") { $lines[$i] = "$Key=$Value"; $updated = $true; break }
  }
  if (-not $updated) { $lines += "$Key=$Value" }
  Set-Content -Path $Path -Value $lines -Encoding UTF8
}

Write-Host "[env] Writing sensitive keys securely to $EnvPath (not echoed)."

# Core
$llm = Read-Host -Prompt "LLM_PROVIDER (gemini|minimax) [leave empty to keep current]"
if ($llm) { Set-EnvVar $EnvPath "LLM_PROVIDER" $llm }

# MiniMax
$minimax = Read-Secret "MINIMAX_API_TOKEN (enter to skip)"
Set-EnvVar $EnvPath "MINIMAX_API_TOKEN" $minimax
$minibase = Read-Host -Prompt "MINIMAX_BASE_URL [default https://api.minimax.io/anthropic]"
if (-not $minibase) { $minibase = "https://api.minimax.io/anthropic" }
Set-EnvVar $EnvPath "MINIMAX_BASE_URL" $minibase
$minimodel = Read-Host -Prompt "MINIMAX_MODEL [default claude-3-haiku-20240307]"
if (-not $minimodel) { $minimodel = "claude-3-haiku-20240307" }
Set-EnvVar $EnvPath "MINIMAX_MODEL" $minimodel
Set-EnvVar $EnvPath "ANTHROPIC_VERSION" "2023-06-01"

# Gemini (optional)
$gk = Read-Secret "GEMINI_API_KEY (enter to skip)"
Set-EnvVar $EnvPath "GEMINI_API_KEY" $gk

# Telegram
$tg = Read-Secret "TELEGRAM_TOKEN (enter to skip)"
Set-EnvVar $EnvPath "TELEGRAM_TOKEN" $tg

# Slack (optional)
$slack = Read-Secret "SLACK_BOT_TOKEN (enter to skip)"
Set-EnvVar $EnvPath "SLACK_BOT_TOKEN" $slack

# Supabase (optional)
$supabaseUrl = Read-Host -Prompt "SUPABASE_URL (enter to skip)"
Set-EnvVar $EnvPath "SUPABASE_URL" $supabaseUrl
$supabaseAnon = Read-Secret "SUPABASE_ANON_KEY (enter to skip)"
Set-EnvVar $EnvPath "SUPABASE_ANON_KEY" $supabaseAnon
$supabaseSrv = Read-Secret "SUPABASE_SERVICE_ROLE_KEY (enter to skip)"
Set-EnvVar $EnvPath "SUPABASE_SERVICE_ROLE_KEY" $supabaseSrv

# Voice (optional)
$eleven = Read-Secret "ELEVENLABS_API_KEY (enter to skip)"
Set-EnvVar $EnvPath "ELEVENLABS_API_KEY" $eleven

# Other LLMs (optional)
$openai = Read-Secret "OPENAI_API_KEY (enter to skip)"
Set-EnvVar $EnvPath "OPENAI_API_KEY" $openai
$openrouter = Read-Secret "OPENROUTER_API_KEY (enter to skip)"
Set-EnvVar $EnvPath "OPENROUTER_API_KEY" $openrouter
$pplx = Read-Secret "PERPLEXITY_API_KEY (enter to skip)"
Set-EnvVar $EnvPath "PERPLEXITY_API_KEY" $pplx

Write-Host "[env] Done. Keys written to $EnvPath"
