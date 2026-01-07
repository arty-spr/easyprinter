param(
    [string]$InstallPath = "C:\Program Files\EasyPrinter",
    [string]$SourcePath = "C:\ProgramData\EasyPrinter-src",
    [string]$RepoUrl = "https://github.com/arty-spr/easyprinter.git"
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

$ErrorActionPreference = "Stop"

trap {
    Write-Host "===========================" -ForegroundColor Red
    Write-Host "ERROR:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "Line: $($_.InvocationInfo.ScriptLineNumber)" -ForegroundColor Yellow
    Write-Host $_.InvocationInfo.Line -ForegroundColor Yellow
    Write-Host "===========================" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

function Info($msg) { Write-Host "[INFO] " -ForegroundColor Cyan -NoNewline; Write-Host $msg }
function Ok($msg)   { Write-Host "[OK] " -ForegroundColor Green -NoNewline; Write-Host $msg }
function Warn($msg) { Write-Host "[!] " -ForegroundColor Yellow -NoNewline; Write-Host $msg }
function Err($msg)  { Write-Host "[X] " -ForegroundColor Red -NoNewline; Write-Host $msg }

Clear-Host
Write-Host "================================================" -ForegroundColor Blue
Write-Host "            EasyPrinter Installation            " -ForegroundColor White
Write-Host "            HP LaserJet M1536dnf MFP            " -ForegroundColor Gray
Write-Host "================================================" -ForegroundColor Blue
Write-Host ""

Info "Checking system..."

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Err "Script must be run as Administrator"
    Read-Host "Press Enter to exit"
    exit 1
}

Info "Checking .NET 6 Desktop Runtime..."

$dotnet = Get-ChildItem "HKLM:\SOFTWARE\dotnet\Setup\InstalledVersions\x64\sharedhost" -ErrorAction SilentlyContinue
if (-not $dotnet) {
    Info ".NET 6 Runtime not found. Installing..."
    $dotnetUrl = "https://download.visualstudio.microsoft.com/download/pr/3c5b2d1a-5c0f-4f9e-9a1e-4d1b0d0a6f4f/2c3e4e5d6f7a8b9c0d1e2f3a4b5c6d7e/windowsdesktop-runtime-6.0.25-win-x64.exe"
    $dotnetInstaller = "$env:TEMP\dotnet6.exe"
    Info "Downloading .NET 6 Runtime..."
    Invoke-WebRequest $dotnetUrl -OutFile $dotnetInstaller
    Info "Running installer..."
    Start-Process $dotnetInstaller -ArgumentList "/install /quiet /norestart" -Wait
    Remove-Item $dotnetInstaller -Force
    Ok ".NET 6 Runtime installed"
} else {
    Ok ".NET 6 Runtime already installed"
}

Info "Checking Git..."

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Info "Git not found. Installing..."
    $gitUrl = "https://github.com/git-for-windows/git/releases/latest/download/Git-2.44.0-64-bit.exe"
    $gitInstaller = "$env:TEMP\git.exe"
    Invoke-WebRequest $gitUrl -OutFile $gitInstaller
    Start-Process $gitInstaller -ArgumentList "/VERYSILENT /NORESTART" -Wait
    Remove-Item $gitInstaller -Force
    Ok "Git installed"
} else {
    Ok "Git already installed"
}

Info "Preparing source code..."

if (Test-Path $SourcePath) {
    Set-Location $SourcePath
    Info "Updating existing repository..."
    git pull
} else {
    Info "Cloning repository..."
    git clone $RepoUrl $SourcePath
    Set-Location $SourcePath
}

Info "Building application..."

$publishPath = "$InstallPath\app"
if (Test-Path $publishPath) {
    Remove-Item $publishPath -Recurse -Force
}

Info "Restoring NuGet packages..."
dotnet restore

Info "Compiling..."
dotnet publish -c Release -r win-x64 --self-contained false -o $publishPath

Ok "Build completed"

Info "Creating shortcuts..."

$exePath = "$publishPath\EasyPrinter.exe"
$desktop = [Environment]::GetFolderPath("Desktop")
$startMenu = "$env:ProgramData\Microsoft\Windows\Start Menu\Programs"

$wsh = New-Object -ComObject WScript.Shell

$desktopShortcut = $wsh.CreateShortcut("$desktop\EasyPrinter.lnk")
$desktopShortcut.TargetPath = $exePath
$desktopShortcut.WorkingDirectory = $publishPath
$desktopShortcut.Save()

$menuShortcut = $wsh.CreateShortcut("$startMenu\EasyPrinter.lnk")
$menuShortcut.TargetPath = $exePath
$menuShortcut.WorkingDirectory = $publishPath
$menuShortcut.Save()

Ok "Shortcuts created"

Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "           Installation Completed!              " -ForegroundColor White
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Installed to: $InstallPath" -ForegroundColor Cyan
Write-Host "Source code:  $SourcePath" -ForegroundColor Cyan
Write-Host ""

$response = Read-Host "Launch EasyPrinter now? (Y/N)"
if ($response -match "^[Yy]$") {
    Start-Process $exePath
}

Read-Host "Press Enter to exit"
