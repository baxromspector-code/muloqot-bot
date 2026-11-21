# MULOQOT: bot, sayt, tunnel va ichki PostgreSQL'ni to'g'ri to'xtatadi.
#   powershell -ExecutionPolicy Bypass -File stop_all.ps1
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
    Where-Object { $_.CommandLine -match 'run_local\.py|run_admin_local\.py|tunnel\.py' } |
    ForEach-Object { taskkill /T /F /PID $_.ProcessId 2>$null | Out-Null }  # /T — sayt ishchi jarayonlari ham
Get-Process cloudflared -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
$pgctl = Get-ChildItem (& python -c "import pgserver,os;print(os.path.dirname(pgserver.__file__))") -Recurse -Filter pg_ctl.exe |
    Select-Object -First 1
if ($pgctl) { & $pgctl.FullName -D (Join-Path $root 'pgdata') stop -m fast -w -t 90 }
Remove-Item (Join-Path $root 'pgdata\.handle_pids.json') -ErrorAction SilentlyContinue
Write-Output "To'xtatildi."
