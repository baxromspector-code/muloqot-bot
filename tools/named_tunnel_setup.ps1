# Doimiy tunnel: o'z domeningizda o'zgarmas https manzil (masalan https://app.muloqotclub.uz).
# Bir marta ishga tushiriladi. Oldin: domen Cloudflare'ga qo'shilgan va nameserverlari Cloudflare'ga o'tkazilgan bo'lsin.
#
#   powershell -ExecutionPolicy Bypass -File tools\named_tunnel_setup.ps1 -Hostname app.muloqotclub.uz
#
# Qadamlar:
#   1) cloudflared tunnel login  — brauzer ochiladi, Cloudflare'da domeningizni tanlab «Authorize» bosasiz (o'zingiz);
#   2) «muloqot» nomli tunnel yaratiladi (kalit fayli %USERPROFILE%\.cloudflared ichida saqlanadi);
#   3) Hostname uchun DNS yozuvi (CNAME) avtomatik qo'shiladi;
#   4) .env ga TUNNEL_NAME, TUNNEL_HOSTNAME, SITE_URL yoziladi — keyin tools\tunnel.py doimiy rejimda ishlaydi.
param(
    [Parameter(Mandatory = $true)][string]$Hostname,
    [string]$Name = 'muloqot'
)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$cf = (Get-Command cloudflared -ErrorAction SilentlyContinue).Source
if (-not $cf) { $cf = 'C:\Program Files (x86)\cloudflared\cloudflared.exe' }
$Hostname = $Hostname -replace '^https?://', '' -replace '/+$', ''

if (-not (Test-Path (Join-Path $env:USERPROFILE '.cloudflared\cert.pem'))) {
    Write-Output "1) Brauzerda Cloudflare ochiladi: domeningizni tanlang va Authorize bosing..."
    & $cf tunnel login
}
$exists = (& $cf tunnel list --output json | ConvertFrom-Json) | Where-Object { $_.name -eq $Name }
if (-not $exists) {
    Write-Output "2) Tunnel yaratilmoqda: $Name"
    & $cf tunnel create $Name
} else { Write-Output "2) Tunnel allaqachon bor: $Name" }
Write-Output "3) DNS: $Hostname -> tunnel $Name"
& $cf tunnel route dns --overwrite-dns $Name $Hostname

$envFile = Join-Path $root '.env'
$text = Get-Content $envFile -Raw -Encoding UTF8
foreach ($kv in @(@('TUNNEL_NAME', $Name), @('TUNNEL_HOSTNAME', $Hostname), @('SITE_URL', "https://$Hostname"))) {
    $k = $kv[0]; $v = $kv[1]
    if ($text -match "(?m)^$k=") { $text = $text -replace "(?m)^$k=.*$", "$k=$v" } else { $text = $text.TrimEnd() + "`n$k=$v`n" }
}
[IO.File]::WriteAllText($envFile, $text, (New-Object Text.UTF8Encoding $false))
Write-Output "4) .env yangilandi. Endi: stop_all.ps1, keyin start_all.ps1 (yoki kompyuterni qayta yoqing)."
Write-Output "   Mini App: https://$Hostname/app"
