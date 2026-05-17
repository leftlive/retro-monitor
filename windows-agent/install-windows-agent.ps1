param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$ServiceName = "RetroMonitorWindowsAgent",
    [string]$PublishDir = "",
    [string]$DotnetPath = "",
    [switch]$SelfContained
)

if (-not $PublishDir) {
    $PublishDir = Join-Path $ProjectRoot "windows-agent\publish"
}

$localDotnet = Join-Path $ProjectRoot ".dotnet\dotnet.exe"
if (-not $DotnetPath) {
    if (Test-Path $localDotnet) {
        $DotnetPath = $localDotnet
    }
    else {
        $DotnetPath = "dotnet"
    }
}

$env:DOTNET_CLI_HOME = Join-Path $ProjectRoot ".dotnet-home"
$env:DOTNET_SKIP_FIRST_TIME_EXPERIENCE = "1"
$env:DOTNET_NOLOGO = "1"
$env:NUGET_PACKAGES = Join-Path $ProjectRoot ".nuget\packages"
$env:APPDATA = Join-Path $ProjectRoot ".appdata"
$env:LOCALAPPDATA = Join-Path $ProjectRoot ".localappdata"
$env:USERPROFILE = Join-Path $ProjectRoot ".userprofile"
New-Item -ItemType Directory -Force -Path `
    $env:DOTNET_CLI_HOME, `
    $env:NUGET_PACKAGES, `
    $env:APPDATA, `
    $env:LOCALAPPDATA, `
    $env:USERPROFILE | Out-Null

$project = Join-Path $ProjectRoot "windows-agent\RetroMonitor.WindowsAgent\RetroMonitor.WindowsAgent.csproj"
$serviceExe = Join-Path $PublishDir "RetroMonitor.WindowsAgent.exe"

if (Get-Service -Name $ServiceName -ErrorAction SilentlyContinue) {
    Stop-Service -Name $ServiceName -Force -ErrorAction SilentlyContinue
    sc.exe delete $ServiceName | Out-Null
    Start-Sleep -Seconds 2
}

$restoreArgs = @(
    "restore",
    $project,
    "-r", "win-x64"
)

$localNugetSource = Join-Path $ProjectRoot ".nuget-source"
if (Test-Path $localNugetSource) {
    $restoreArgs += "--source"
    $restoreArgs += $localNugetSource
}

& $DotnetPath @restoreArgs
if ($LASTEXITCODE -ne 0) {
    throw "dotnet restore failed"
}

$publishArgs = @(
    "publish",
    $project,
    "-c", "Release",
    "-r", "win-x64",
    "-o", $PublishDir,
    "--no-restore",
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

& $DotnetPath @publishArgs
if ($LASTEXITCODE -ne 0) {
    throw "dotnet publish failed"
}

sc.exe create $ServiceName binPath= "`"$serviceExe`"" start= auto | Out-Null
sc.exe description $ServiceName "Retro Monitor Windows telemetry agent" | Out-Null
Start-Service -Name $ServiceName

Write-Host "Installed service $ServiceName"
