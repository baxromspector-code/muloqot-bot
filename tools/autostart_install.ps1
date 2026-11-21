# Windows'ga kirganda start_all.ps1 o'zi ishga tushishi uchun «Автозагрузка» (Startup) papkasiga yorliq qo'yadi.
#   o'rnatish:  powershell -ExecutionPolicy Bypass -File tools\autostart_install.ps1
#   olib tashlash: powershell -ExecutionPolicy Bypass -File tools\autostart_install.ps1 -Remove
# Loyiha papkasi ko'chirilsa - shu skriptni yangi joydan qayta ishga tushiring.
param([switch]$Remove)
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$lnk = Join-Path ([Environment]::GetFolderPath('Startup')) 'MULOQOT bot.lnk'
if ($Remove) { Remove-Item $lnk -ErrorAction SilentlyContinue; Write-Output "Avtoyuklash olib tashlandi."; exit }
$sh = New-Object -ComObject WScript.Shell
$s = $sh.CreateShortcut($lnk)
$s.TargetPath = Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
$s.Arguments = "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$(Join-Path $root 'start_all.ps1')`""
$s.WorkingDirectory = $root
$s.WindowStyle = 7
$s.Description = 'MULOQOT: bot, sayt va Mini App tunnelini ishga tushiradi'
$s.Save()
Write-Output "Avtoyuklash o'rnatildi: $lnk"
