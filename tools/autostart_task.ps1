# Kompyuter YONISHI BILAN (Windows'ga kirmasdan ham) start_all.ps1 ni ishga tushiradigan vazifa — Windows «Планировщик заданий».
# Parol saqlanmaydi: S4U rejimi («пользователь не вошёл в систему» + «не сохранять пароль») — faqat shu kompyuter ichida ishlaydi.
# Administrator ruxsati kerak (UAC).
#   o'rnatish:    powershell -ExecutionPolicy Bypass -File tools\autostart_task.ps1
#   olib tashlash: powershell -ExecutionPolicy Bypass -File tools\autostart_task.ps1 -Remove
param([switch]$Remove, [string]$User = "$env:USERDOMAIN\$env:USERNAME")
$ErrorActionPreference = 'Stop'
$name = 'MULOQOT bot (kompyuter yonganda)'
if ($Remove) {
    Unregister-ScheduledTask -TaskName $name -Confirm:$false -ErrorAction SilentlyContinue
    Write-Output "Vazifa olib tashlandi."
    exit
}
$root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$ps = Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
$action = New-ScheduledTaskAction -Execute $ps -WorkingDirectory $root `
    -Argument "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -File `"$(Join-Path $root 'start_all.ps1')`""
$trigger = New-ScheduledTaskTrigger -AtStartup
$trigger.Delay = 'PT1M'                                     # tarmoq va Tailscale ulanib olishi uchun 1 daqiqa
$principal = New-ScheduledTaskPrincipal -UserId $User -LogonType S4U -RunLevel Limited
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable `
    -ExecutionTimeLimit ([TimeSpan]::Zero) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 5) `
    -MultipleInstances IgnoreNew
Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Principal $principal -Settings $settings `
    -Description 'MULOQOT: bot, sayt (Mini App) — kompyuter yonganda, Windows''ga kirilmasa ham. start_all.ps1 ikki marta ishga tushmaydi.' `
    -Force | Out-Null
Write-Output "Vazifa o'rnatildi: $name ($User, S4U, yonganda + 1 daqiqa)"
