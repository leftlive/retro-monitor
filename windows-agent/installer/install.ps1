param(
    [string]$InstallDir = "$env:ProgramFiles\RetroMonitor\WindowsAgent",
    [string]$ServiceName = "RetroMonitorWindowsAgent",
    [string]$DisplayName = "Retro Monitor Windows Agent",
    [int]$Port = 8125,
    [switch]$SkipFirewallRule
)

$ErrorActionPreference = "Stop"

function Test-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Administrator)) {
    throw "Please run this installer from an elevated PowerShell window."
}

$packageRoot = $PSScriptRoot
$appSource = Join-Path $packageRoot "app"
$sourceExe = Join-Path $appSource "RetroMonitor.WindowsAgent.exe"

if (-not (Test-Path $sourceExe)) {
    throw "Cannot find packaged app at $sourceExe"
}

if (Get-Service -Name $ServiceName -ErrorAction SilentlyContinue) {
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    sc.exe delete $ServiceName | Out-Null
    Start-Sleep -Seconds 2
}

New-Item -ItemType Directory -Force -Path $InstallDir | Out-Null
Copy-Item -Path (Join-Path $appSource "*") -Destination $InstallDir -Recurse -Force

$serviceExe = Join-Path $InstallDir "RetroMonitor.WindowsAgent.exe"
sc.exe create $ServiceName binPath= "`"$serviceExe`"" start= auto DisplayName= "`"$DisplayName`"" | Out-Null
if ($LASTEXITCODE -ne 0) {
    throw "Failed to create service $ServiceName"
}

sc.exe description $ServiceName "Retro Monitor Windows telemetry agent" | Out-Null

if (-not $SkipFirewallRule) {
    $ruleName = "Retro Monitor Windows Agent (TCP $Port)"
    try {
        $existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
        if (-not $existingRule) {
            New-NetFirewallRule `
                -DisplayName $ruleName `
                -Direction Inbound `
                -Action Allow `
                -Protocol TCP `
                -LocalPort $Port | Out-Null
        }
    }
    catch {
        Write-Warning "Could not create firewall rule for TCP ${Port}: $($_.Exception.Message)"
    }
}

Start-Service -Name $ServiceName
Start-Sleep -Seconds 3

$service = Get-Service -Name $ServiceName
Write-Host "Installed $DisplayName"
Write-Host "Service: $($service.Name) / $($service.Status) / startup: Automatic"
Write-Host "Install directory: $InstallDir"
Write-Host "Telemetry URL: http://127.0.0.1:$Port/telemetry"
