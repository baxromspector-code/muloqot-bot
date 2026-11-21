# MULOQOT: tunnel, bot va saytni yashirin oynada ishga tushiradi (Windows avtoyuklash shu faylni chaqiradi).
# Qo'lda:  powershell -ExecutionPolicy Bypass -File start_all.ps1
# To'xtatish: stop_all.ps1     Jurnallar: autostart.log, tunnel.out.log, bot.log, admin.log
$ErrorActionPreference = 'Continue'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root
$log = Join-Path $root 'autostart.log'
function Log($m) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m" | Out-File -Append -Encoding utf8 $log }

$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $py) { $py = Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe' }
$env:PYTHONIOENCODING = 'utf-8'
$env:PYTHONUNBUFFERED = '1'

function Wait-For($what, $seconds, [scriptblock]$test) {
    for ($i = 0; $i -lt $seconds; $i += 2) { if (& $test) { return $true }; Start-Sleep 2 }
    Log "KUTISH TUGADI: $what"; return $false
}
function Has($file, $text) { (Test-Path $file) -and (Select-String -Path $file -Pattern $text -SimpleMatch -Quiet) }

# 0) bot Render'ga ko'chirilgan bo'lsa (.env: HOSTED=render) — noutbukda ishga tushirmaymiz:
#    bu yerdagi polling Render'dagi webhook'ni o'chirib, botni o'ziga tortib olardi.
if ((Get-Content (Join-Path $root '.env') -ErrorAction SilentlyContinue) -match '^HOSTED=render') {
    Log 'HOSTED=render - bot Render serverida ishlaydi, noutbukda ishga tushirilmadi'; exit
}

# 1) ikki marta ishga tushmasin
$mine = Get-CimInstance Win32_Process -Filter "Name='python.exe'" |
    Where-Object { $_.CommandLine -match 'run_local\.py|run_admin_local\.py|tunnel\.py' }
if ($mine) { Log 'Allaqachon ishlayapti - chiqildi'; exit }
Log '--- ishga tushirish ---'

# 2) internet paydo bo'lishini kutamiz (kompyuter endi yongan bo'lishi mumkin)
Wait-For 'internet' 300 {
    try { Invoke-WebRequest 'https://api.telegram.org' -UseBasicParsing -TimeoutSec 5 | Out-Null; $true } catch { $_.Exception.Response -ne $null }
} | Out-Null

# 3) kompyuter keskin o'chgan bo'lsa PostgreSQL'ning eski qulf fayllarini tozalaymiz
if (-not (Get-Process postgres -ErrorAction SilentlyContinue)) {
    Remove-Item (Join-Path $root 'pgdata\postmaster.pid') -ErrorAction SilentlyContinue
    Remove-Item (Join-Path $root 'pgdata\.handle_pids.json') -ErrorAction SilentlyContinue
}

function Start-Hidden($script, $out) {
    Remove-Item $out -ErrorAction SilentlyContinue
    # cmd /c butun buyruqni yana bir juft qo'shtirnoqqa o'rashni talab qiladi (aks holda qo'shtirnoqlarni yeb qo'yadi)
    Start-Process cmd.exe -ArgumentList "/c `"`"$py`" $script > `"$out`" 2>&1`"" -WindowStyle Hidden -WorkingDirectory $root
}

# 4) tashqi https manzil.
#    .env da TUNNEL=tailscale bo'lsa — Tailscale Funnel (Windows xizmati, o'zi ishga tushadi, manzil o'zgarmaydi);
#    aks holda — Cloudflare tunnel (tools\tunnel.py): yangi manzil -> .env SITE_URL va botdagi «Ilova» tugmasi.
$tunnelMode = ((Get-Content (Join-Path $root '.env') -ErrorAction SilentlyContinue) | Where-Object { $_ -like 'TUNNEL=*' } |
    Select-Object -First 1) -replace '^TUNNEL=', ''
if ($tunnelMode -eq 'tailscale') {
    $ts = Join-Path $env:ProgramFiles 'Tailscale\tailscale.exe'
    if (Test-Path $ts) { & $ts funnel --bg 8080 2>&1 | Out-Null }  # sozlama saqlanadi; bu faqat kafolat uchun
    Log 'Tashqi manzil: Tailscale Funnel'
} else {
    Start-Hidden 'tools\tunnel.py' (Join-Path $root 'tunnel.out.log')
    if (Wait-For 'tunnel' 120 { Has 'tunnel.out.log' 'Tunnel manzili' }) {
        Log ((Select-String -Path 'tunnel.out.log' -Pattern 'trycloudflare' | Select-Object -First 1).Line.Trim())
    }
}

# 5) bot (yangi SITE_URL bilan)
Start-Hidden 'run_local.py' (Join-Path $root 'bot.log')
if (Wait-For 'bot' 240 { Has 'bot.log' 'Run polling' }) { Log 'Bot ishga tushdi' }

# 6) sayt va Mini App
Start-Hidden 'run_admin_local.py' (Join-Path $root 'admin.log')
if (Wait-For 'sayt' 120 {
    try { (Invoke-WebRequest 'http://127.0.0.1:8080/' -UseBasicParsing -TimeoutSec 5).StatusCode -eq 200 } catch { $false }
}) { Log 'Sayt ishga tushdi (8080)' }
Log '--- tayyor ---'
