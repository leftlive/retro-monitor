param(
    [string]$InstallDir = "$env:ProgramFiles\RetroMonitor\WindowsAgent",
    [string]$ServiceName = "RetroMonitorWindowsAgent",
    [int]$Port = 8125,
    [switch]$KeepFiles,
    [switch]$KeepFirewallRule
)

$ErrorActionPreference = "Stop"

function Test-Administrator {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]::new($identity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-Administrator)) {
    throw "Please run this uninstaller from an elevated PowerShell window."
}

if (Get-Service -Name $ServiceName -ErrorAction SilentlyContinue) {
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    sc.exe delete $ServiceName | Out-Null
    Start-Sleep -Seconds 2
}

if (-not $KeepFirewallRule) {
    $ruleName = "Retro Monitor Windows Agent (TCP $Port)"
    Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue |
        Remove-NetFirewallRule -ErrorAction SilentlyContinue
}

if (-not $KeepFiles -and (Test-Path $InstallDir)) {
    Remove-Item -LiteralPath $InstallDir -Recurse -Force
}

Write-Host "Removed $ServiceName"
