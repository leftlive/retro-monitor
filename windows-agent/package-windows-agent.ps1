param(
    [string]$ProjectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path,
    [string]$PackageRoot = "",
    [string]$DotnetPath = ""
)

$ErrorActionPreference = "Stop"

if (-not $PackageRoot) {
    $PackageRoot = Join-Path $ProjectRoot "windows-agent\package\RetroMonitorWindowsAgent"
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
$publishDir = Join-Path $ProjectRoot "windows-agent\package-build\publish"
$installerDir = Join-Path $ProjectRoot "windows-agent\installer"
$appDir = Join-Path $PackageRoot "app"

New-Item -ItemType Directory -Force -Path $publishDir | Out-Null

$restoreArgs = @("restore", $project, "-r", "win-x64")
$localNugetSource = Join-Path $ProjectRoot ".nuget-source"
if (Test-Path $localNugetSource) {
    $restoreArgs += "--source"
    $restoreArgs += $localNugetSource
}

& $DotnetPath @restoreArgs
if ($LASTEXITCODE -ne 0) {
    throw "dotnet restore failed"
}

& $DotnetPath publish $project `
    -c Release `
    -r win-x64 `
    -o $publishDir `
    --no-restore `
    --self-contained true `
    /p:PublishSingleFile=true
if ($LASTEXITCODE -ne 0) {
    throw "dotnet publish failed"
}

if (Test-Path $PackageRoot) {
    Remove-Item -LiteralPath $PackageRoot -Recurse -Force
}

New-Item -ItemType Directory -Force -Path $appDir | Out-Null
Copy-Item -Path (Join-Path $publishDir "*") -Destination $appDir -Recurse -Force
Copy-Item -LiteralPath (Join-Path $installerDir "install.ps1") -Destination $PackageRoot -Force
Copy-Item -LiteralPath (Join-Path $installerDir "uninstall.ps1") -Destination $PackageRoot -Force

$zipPath = "$PackageRoot.zip"
if (Test-Path $zipPath) {
    Remove-Item -LiteralPath $zipPath -Force
}
Compress-Archive -LiteralPath $PackageRoot -DestinationPath $zipPath -Force

Write-Host "Package directory: $PackageRoot"
Write-Host "Package archive: $zipPath"
