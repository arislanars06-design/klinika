<#
  NURMED serverini Windows'da fonda boshqarish (PowerShell oynasisiz).

  Server Task Scheduler'dagi "NURMED" vazifasi sifatida ishlaydi:
    - kompyuter yoqilganda o'zi ishga tushadi (hech kim tizimga kirmasa ham);
    - oyna ochilmaydi, PowerShell'ni yopish mumkin;
    - to'xtab qolsa, 1 daqiqadan keyin qayta ishga tushadi;
    - jurnal: data\logs\server.log

  Ishlatish (.bat fayllar shu skriptni chaqiradi):
    install    - o'rnatish va ishga tushirish (bir marta)
    restart    - qayta ishga tushirish
    update     - git pull + qayta ishga tushirish (yangilash)
    status     - holatini ko'rsatish
    uninstall  - olib tashlash
#>
param(
  [ValidateSet('install', 'restart', 'update', 'status', 'uninstall')]
  [string]$Action = 'status',
  [int]$Port = 3000
)

$ErrorActionPreference = 'Stop'
$TaskName = 'NURMED'
$Root = Split-Path -Parent $PSScriptRoot
$Runner = Join-Path $PSScriptRoot 'run-server.cmd'
$Log = Join-Path $Root 'data\logs\server.log'

function Pause-End {
  Write-Host ''
  Read-Host 'Oynani yopish uchun Enter tugmasini bosing' | Out-Null
}

# Administrator huquqi kerak: bo'lmasa, o'zini administrator sifatida qayta ochadi
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
  [Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
  Write-Host 'Administrator huquqi so''ralmoqda...'
  $argList = @('-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', "`"$PSCommandPath`"", '-Action', $Action, '-Port', $Port)
  Start-Process -FilePath 'powershell.exe' -Verb RunAs -ArgumentList $argList
  exit
}

function Get-ServerProcesses {
  # Shu papkadagi server.js ni ishlatayotgan node jarayonlari (npm start oynasidagisi ham)
  Get-CimInstance Win32_Process -Filter "Name = 'node.exe'" |
    Where-Object { $_.CommandLine -and $_.CommandLine -like '*server*server.js*' }
}

function Stop-Server {
  $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
  if ($task -and $task.State -eq 'Running') { Stop-ScheduledTask -TaskName $TaskName }
  # Vazifa to'xtatilganda node jarayoni ba'zan qolib ketadi, shuning uchun alohida to'xtatamiz
  foreach ($p in Get-ServerProcesses) {
    Write-Host "  node jarayoni to'xtatilmoqda (PID $($p.ProcessId))"
    Stop-Process -Id $p.ProcessId -Force -ErrorAction SilentlyContinue
  }
  Start-Sleep -Seconds 2
}

function Test-Server {
  for ($i = 0; $i -lt 20; $i++) {
    try {
      $r = Invoke-WebRequest -Uri "http://localhost:$Port/" -UseBasicParsing -TimeoutSec 3
      if ($r.StatusCode -eq 200) { return $true }
    } catch { }
    Start-Sleep -Seconds 1
  }
  return $false
}

function Show-Addresses {
  $ips = Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*' } |
    Select-Object -ExpandProperty IPAddress
  Write-Host ''
  Write-Host 'Boshqa kompyuterlarda brauzerda oching:' -ForegroundColor Cyan
  foreach ($ip in $ips) { Write-Host "  http://${ip}:$Port" -ForegroundColor Cyan }
  Write-Host "  (shu kompyuterda: http://localhost:$Port)"
}

function Start-Server {
  Start-ScheduledTask -TaskName $TaskName
  if (Test-Server) {
    Write-Host ''
    Write-Host 'NURMED ishlayapti. PowerShell oynasini yopishingiz mumkin.' -ForegroundColor Green
    Show-Addresses
  } else {
    Write-Host ''
    Write-Host 'Server javob bermadi. Jurnalni tekshiring:' -ForegroundColor Red
    Write-Host "  $Log"
    if (Test-Path $Log) { Get-Content $Log -Tail 20 }
  }
}

try {
  switch ($Action) {
    'install' {
      # Avval o'rnatilgan Node.js (Program Files), bo'lmasa PATH dagisi
      $node = Join-Path $env:ProgramFiles 'nodejs\node.exe'
      if (-not (Test-Path $node)) { $node = (Get-Command node -ErrorAction SilentlyContinue).Source }
      if (-not $node) { throw 'Node.js topilmadi. Avval https://nodejs.org dan Node.js 22 yoki 24 (LTS) ni o''rnating.' }
      $ver = (& $node --version).Trim()
      Write-Host "Node.js: $node ($ver)"
      $m = [regex]::Match($ver, '^v(\d+)\.(\d+)')
      if (-not $m.Success -or [int]$m.Groups[1].Value -lt 22 -or ([int]$m.Groups[1].Value -eq 22 -and [int]$m.Groups[2].Value -lt 13)) {
        throw "Node.js $ver eski. Node.js 22.13 yoki undan yangisi kerak: https://nodejs.org (LTS) dan o'rnating."
      }
      if ($env:USERPROFILE -and $node -like "$env:USERPROFILE*") {
        Write-Host 'Diqqat: Node.js foydalanuvchi papkasida turibdi. Uni o''chirib yuborsangiz, server ishlamay qoladi.' -ForegroundColor Yellow
        Write-Host 'Yaxshisi https://nodejs.org dan Node.js LTS ni o''rnating va install.bat ni qayta bosing.' -ForegroundColor Yellow
      }
      Write-Host "Papka:   $Root"

      Write-Host 'Eski nusxa (npm start oynasi) bo''lsa, to''xtatilmoqda...'
      Stop-Server

      # Diqqat: PowerShell'da $action va $Action bitta o'zgaruvchi, shuning uchun boshqa nomlar
      $taskAction = New-ScheduledTaskAction -Execute $Runner -Argument "`"$node`"" -WorkingDirectory $Root
      $taskTrigger = New-ScheduledTaskTrigger -AtStartup
      $taskPrincipal = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
      $taskSettings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable `
        -RestartCount 999 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit (New-TimeSpan -Seconds 0) `
        -MultipleInstances IgnoreNew
      Register-ScheduledTask -TaskName $TaskName -Action $taskAction -Trigger $taskTrigger -Principal $taskPrincipal -Settings $taskSettings `
        -Description 'NURMED LOR klinikasi serveri (fonda, kompyuter yoqilganda ishga tushadi)' -Force | Out-Null
      Write-Host "Task Scheduler'da '$TaskName' vazifasi yaratildi."

      # Lokal tarmoq uchun port (Private va Domain tarmoq profillari)
      $rule = "NURMED (TCP $Port)"
      if (-not (Get-NetFirewallRule -DisplayName $rule -ErrorAction SilentlyContinue)) {
        New-NetFirewallRule -DisplayName $rule -Direction Inbound -Protocol TCP -LocalPort $Port -Action Allow -Profile Private, Domain | Out-Null
        Write-Host "Firewall'da $Port-port lokal tarmoq uchun ochildi."
      }
      Start-Server
    }
    'restart' {
      if (-not (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue)) { throw 'NURMED vazifasi o''rnatilmagan. Avval install.bat ni ishga tushiring.' }
      Write-Host 'Qayta ishga tushirilmoqda...'
      Stop-Server
      Start-Server
    }
    'update' {
      if (-not (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue)) { throw 'NURMED vazifasi o''rnatilmagan. Avval install.bat ni ishga tushiring.' }
      Push-Location $Root
      try {
        Write-Host 'Yangilanish yuklanmoqda (git pull)...'
        & git pull
        if ($LASTEXITCODE -ne 0) { throw 'git pull bajarilmadi. Yuqoridagi xabarni o''qing.' }
      } finally { Pop-Location }
      Stop-Server
      Start-Server
    }
    'status' {
      $task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
      if (-not $task) { Write-Host 'NURMED vazifasi o''rnatilmagan.' -ForegroundColor Yellow }
      else {
        $info = Get-ScheduledTaskInfo -TaskName $TaskName
        Write-Host "Vazifa holati: $($task.State); oxirgi ishga tushish: $($info.LastRunTime)"
      }
      $procs = @(Get-ServerProcesses)
      if ($procs.Count) { Write-Host "Server ishlayapti (PID $($procs.ProcessId -join ', '))." -ForegroundColor Green; Show-Addresses }
      else { Write-Host 'Server ishlamayapti.' -ForegroundColor Red }
      if (Test-Path $Log) { Write-Host ''; Write-Host "Jurnalning oxiri ($Log):"; Get-Content $Log -Tail 10 }
    }
    'uninstall' {
      Stop-Server
      if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) { Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false }
      Write-Host 'NURMED vazifasi olib tashlandi. Server endi o''zi ishga tushmaydi (ma''lumotlar o''chmaydi).'
    }
  }
} catch {
  Write-Host ''
  Write-Host "Xato: $($_.Exception.Message)" -ForegroundColor Red
}
Pause-End
