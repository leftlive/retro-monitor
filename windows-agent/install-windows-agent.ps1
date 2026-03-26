param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$ServiceName = "RetroMonitorWindowsAgent",
    [string]$PublishDir = "",
    [switch]$SelfContained
)

if (-not $PublishDir) {
    $PublishDir = Join-Path $ProjectRoot "windows-agent\publish"
}

$project = Join-Path $ProjectRoot "windows-agent\RetroMonitor.WindowsAgent\RetroMonitor.WindowsAgent.csproj"
$serviceExe = Join-Path $PublishDir "RetroMonitor.WindowsAgent.exe"

if (Get-Service -Name $ServiceName -ErrorAction SilentlyContinue) {
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    sc.exe delete $ServiceName | Out-Null
    Start-Sleep -Seconds 2
}

$publishArgs = @(
    "publish",
    $project,
    "-c", "Release",
    "-r", "win-x64",
    "-o", $PublishDir,
    "/p:PublishSingleFile=true"
)

if ($SelfContained) {
    $publishArgs += "--self-contained"
    $publishArgs += "true"
}
else {
    $publishArgs += "--self-contained"
    $publishArgs += "false"
}

dotnet @publishArgs
if ($LASTEXITCODE -ne 0) {
    throw "dotnet publish failed"
}

sc.exe create $ServiceName binPath= "`"$serviceExe`"" start= auto | Out-Null
sc.exe description $ServiceName "Retro Monitor Windows telemetry agent" | Out-Null
Start-Service -Name $ServiceName

Write-Host "Installed service $ServiceName"
