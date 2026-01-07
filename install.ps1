#Requires -RunAsAdministrator
<#
.SYNOPSIS
    EasyPrinter Installer Script
.DESCRIPTION
    Installs dependencies, downloads source code, builds the EasyPrinter app,
    and creates shortcuts for HP LaserJet M1536dnf MFP control panel.
.NOTES
    Must be run as Administrator.
#>

# Fix UTF-8 output
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

# Ensure TLS 1.2
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

trap {
    Write-Host ""
    Write-Host "========== ERROR ==========" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "Line: $($_.InvocationInfo.ScriptLineNumber)" -ForegroundColor Yellow
    Write-Host $_.InvocationInfo.Line -ForegroundColor Yellow
    Write-Host "===========================" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

$ErrorActionPreference = "Stop"

param(
    [string]$InstallPath = "C:\Program Files\EasyPrinter",
    [string]$SourcePath = "C:\ProgramData\EasyPrinter-src",
    [string]$RepoUrl = "https://github.com/arty-spr/easyprinter.git"
)

function Info($msg) { Write-Host "[INFO] " -ForegroundColor Cyan -NoNewline; Write-Host $msg }
function Ok($msg)   { Write-Host "[OK] "   -ForegroundColor Green -NoNewline; Write-Host $msg }
function Warn($msg) { Write-Host "[!] "    -ForegroundColor Yellow -NoNewline; Write-Host $msg }
function Err($msg)  { Write-Host "[X] "    -ForegroundColor Red -NoNewline; Write-Host $msg }

Clear-Host
Write-Host "================================================" -ForegroundColor Blue
Write-Host "            EasyPrinter Installation            " -ForegroundColor White
Write-Host "            HP LaserJet M1536dnf MFP            " -ForegroundColor Gray
Write-Host "================================================" -ForegroundColor Blue
Write-Host ""

# 1. System check
Info "Checking system..."
$os = Get-CimInstance Win32_OperatingSystem
$arch = (Get-CimInstance Win32_Processor).AddressWidth

if ($arch -ne 64) {
    Err "64-bit Windows is required"
    exit 1
}

$winVersion = [System.Environment]::OSVersion.Version
if ($winVersion.Major -lt 10) {
    Err "Windows 10 or newer is required"
    exit 1
}

Ok "Windows detected: $($os.Caption) x64"

# 2. Check .NET 6 Desktop Runtime
Info "Checking .NET 6 Desktop Runtime..."
$dotnetInstalled = $false

try {
    $runtimes = & dotnet --list-runtimes 2>$null
    if ($runtimes -match "Microsoft.WindowsDesktop.App 6\.") {
        $dotnetInstalled = $true
        Ok ".NET 6 Desktop Runtime is already installed"
    }
} catch {}

if (-not $dotnetInstalled) {
    Info ".NET 6 Runtime not found. Installing..."

    $dotnetUrl = "https://dotnetcli.azureedge.net/dotnet/WindowsDesktop/6.0.33/windowsdesktop-runtime-6.0.33-win-x64.exe"
    $dotnetInstaller = "$env:TEMP\dotnet6-runtime.exe"

    try {
        Info "Downloading .NET 6 Runtime..."
        Invoke-WebRequest -Uri $dotnetUrl -OutFile $dotnetInstaller

        Info "Running installer..."
        Start-Process -FilePath $dotnetInstaller -ArgumentList "/install /quiet /norestart" -Wait

        Remove-Item $dotnetInstaller -Force
        Ok ".NET 6 Desktop Runtime installed"
    } catch {
        Err "Failed to install .NET 6 Runtime: $_"
        Warn "Install manually: https://dotnet.microsoft.com/download/dotnet/6.0"
        exit 1
    }
}

# 3. Check Git
Info "Checking Git..."
try {
    $gitVersion = & git --version 2>$null
    if ($gitVersion) {
        Ok "Git installed: $gitVersion"
    }
} catch {
    Err "Git is not installed!"
    Warn "Install Git: https://git-scm.com/download/win"
    exit 1
}

# 4. Clone or update repo
Info "Preparing source code..."

if (Test-Path $SourcePath) {
    Info "Updating existing repository..."
    Push-Location $SourcePath
    & git pull origin main
    Pop-Location
} else {
    Info "Cloning repository..."
    & git clone $RepoUrl $SourcePath

    if ($LASTEXITCODE -ne 0) {
        Err "Failed to clone the repository"
        exit 1
    }
}

Ok "Source code ready"

# 5. Build app
Info "Building application..."

$projectPath = Join-Path $SourcePath "src\EasyPrinter\EasyPrinter.csproj"

if (-not (Test-Path $projectPath)) {
    Err "Project file not found: $projectPath"
    exit 1
}

Push-Location (Join-Path $SourcePath "src\EasyPrinter")

try {
    Info "Restoring NuGet packages..."
    & dotnet restore
    if ($LASTEXITCODE -ne 0) { throw "Package restore failed" }

    Info "Compiling..."
    & dotnet publish -c Release -o $InstallPath --self-contained false
    if ($LASTEXITCODE -ne 0) { throw "Build failed" }

    Ok "Application built successfully"
} catch {
    Err "Build error: $_"
    Pop-Location
    exit 1
}

Pop-Location

# 6. Desktop shortcut
Info "Creating desktop shortcut..."

$desktop = [Environment]::GetFolderPath("CommonDesktopDirectory")
$shortcutPath = Join-Path $desktop "EasyPrinter.lnk"
$exePath = Join-Path $InstallPath "EasyPrinter.exe"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $exePath
$shortcut.WorkingDirectory = $InstallPath
$shortcut.Description = "EasyPrinter Control Panel"
$shortcut.Save()

Ok "Desktop shortcut created"

# 7. Update shortcut
Info "Creating update shortcut..."

$updateShortcut = Join-Path $InstallPath "Update EasyPrinter.lnk"
$updateScript = Join-Path $SourcePath "update.ps1"

$shortcut2 = $shell.CreateShortcut($updateShortcut)
$shortcut2.TargetPath = "powershell.exe"
$shortcut2.Arguments = "-ExecutionPolicy Bypass -File `"$updateScript`""
$shortcut2.WorkingDirectory = $SourcePath
$shortcut2.Description = "Update EasyPrinter"
$shortcut2.Save()

Ok "Update shortcut created"

# Finish
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