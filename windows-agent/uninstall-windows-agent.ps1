param(
    [string]$ServiceName = "RetroMonitorWindowsAgent"
)

if (Get-Service -Name $ServiceName -ErrorAction SilentlyContinue) {
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    sc.exe delete $ServiceName | Out-Null
    Write-Host "Removed service $ServiceName"
}
else {
    Write-Host "Service $ServiceName not found"
}
