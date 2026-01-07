param(
    [string]$InstallPath = "C:\Program Files\EasyPrinter",
    [string]$SourcePath = "C:\ProgramData\EasyPrinter-src",
    [string]$RepoUrl = "https://github.com/arty-spr/easyprinter.git"
)

[Console]::OutputEncoding = [System.Text.Encoding]::UTF8
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ErrorActionPreference = "Stop"

trap {
    Write-Host "ERROR:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host $_.InvocationInfo.Line -ForegroundColor Yellow
    Read-Host "Press Enter to exit"
    exit 1
}

function Info($t){ Write-Host "[INFO] $t" -ForegroundColor Cyan }
function Ok($t){ Write-Host "[OK] $t" -ForegroundColor Green }
function Err($t){ Write-Host "[ERROR] $t" -ForegroundColor Red }

Clear-Host
Info "Checking system..."

$admin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole(
    [Security.Principal.WindowsBuiltInRole]::Administrator
)

if (-not $admin) {
    Err "Run PowerShell as Administrator"
    exit 1
}

Info "Checking .NET 6 Desktop Runtime..."

$dotnetOk = $false
$dotnetList = & dotnet --list-runtimes 2>$null
if ($dotnetList) {
    foreach ($line in $dotnetList) {
        if ($line -match "^Microsoft.WindowsDesktop.App 6\.") {
            $dotnetOk = $true
            break
        }
    }
}

if (-not $dotnetOk) {
    Info ".NET 6 Desktop Runtime not found"
    $dotnetUrl = "https://aka.ms/dotnet/6.0/windowsdesktop-runtime-win-x64.exe"
    $dotnetInstaller = "$env:TEMP\windowsdesktop-runtime-6.exe"
    Info "Downloading .NET 6 Desktop Runtime..."
    Invoke-WebRequest -Uri $dotnetUrl -OutFile $dotnetInstaller
    Info "Installing .NET 6 Desktop Runtime..."
    Start-Process $dotnetInstaller -ArgumentList "/install /quiet /norestart" -Wait
    Remove-Item $dotnetInstaller -Force
    Ok ".NET 6 Desktop Runtime installed"
} else {
    Ok ".NET 6 Desktop Runtime already installed"
}

Info "Checking Git..."

if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Info "Git not found"
    $gitUrl = "https://github.com/git-for-windows/git/releases/latest/download/Git-64-bit.exe"
    $gitInstaller = "$env:TEMP\git.exe"
    Info "Downloading Git..."
    Invoke-WebRequest -Uri $gitUrl -OutFile $gitInstaller
    Info "Installing Git..."
    Start-Process $gitInstaller -ArgumentList "/VERYSILENT /NORESTART" -Wait
    Remove-Item $gitInstaller -Force
    Ok "Git installed"
} else {
    Ok "Git already installed"
}

Info "Preparing source directory..."

if (Test-Path $SourcePath) {
    Set-Location $SourcePath
    git pull
} else {
    git clone $RepoUrl $SourcePath
    Set-Location $SourcePath
}

Info "Building application..."

$publishPath = "$InstallPath\app"
if (Test-Path $publishPath) {
    Remove-Item $publishPath -Recurse -Force
}

dotnet restore
dotnet publish -c Release -r win-x64 --self-contained false -o $publishPath

$exePath = "$publishPath\EasyPrinter.exe"
if (-not (Test-Path $exePath)) {
    Err "Build failed: EasyPrinter.exe not found"
    exit 1
}

Info "Creating shortcuts..."

$wsh = New-Object -ComObject WScript.Shell
$desktop = [Environment]::GetFolderPath("Desktop")
$startMenu = "$env:ProgramData\Microsoft\Windows\Start Menu\Programs"

$s1 = $wsh.CreateShortcut("$desktop\EasyPrinter.lnk")
$s1.TargetPath = $exePath
$s1.WorkingDirectory = $publishPath
$s1.Save()

$s2 = $wsh.CreateShortcut("$startMenu\EasyPrinter.lnk")
$s2.TargetPath = $exePath
$s2.WorkingDirectory = $publishPath
$s2.Save()

Ok "Installation completed"

$run = Read-Host "Launch EasyPrinter now? (Y/N)"
if ($run -match "^[Yy]$") {
    Start-Process $exePath
}

Read-Host "Press Enter to exit"
