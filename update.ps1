<#
.SYNOPSIS
    Update script for EasyPrinter
.DESCRIPTION
    Downloads latest version from Git and rebuilds the application
#>

# Global error handler
trap {
    Write-Host ""
    Write-Host "========== ERROR ==========" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host "===========================" -ForegroundColor Red
    Read-Host "Press Enter to exit"
    exit 1
}

$ErrorActionPreference = "Stop"

param(
    [string]$InstallPath = "C:\Program Files\EasyPrinter",
    [string]$SourcePath = "C:\ProgramData\EasyPrinter-src"
)

function Write-Success($message) {
    Write-Host "[OK] " -ForegroundColor Green -NoNewline
    Write-Host $message
}

function Write-Info($message) {
    Write-Host "[INFO] " -ForegroundColor Cyan -NoNewline
    Write-Host $message
}

function Write-Err($message) {
    Write-Host "[X] " -ForegroundColor Red -NoNewline
    Write-Host $message
}

# Banner
Clear-Host
Write-Host "================================================" -ForegroundColor Blue
Write-Host "      EasyPrinter - Update" -ForegroundColor White
Write-Host "================================================" -ForegroundColor Blue
Write-Host ""

# Check source folder
if (-not (Test-Path $SourcePath)) {
    Write-Err "Source code not found: $SourcePath"
    Write-Host "Please run install.ps1 first"
    Read-Host "Press Enter to exit"
    exit 1
}

# 1. Close EasyPrinter if running
Write-Info "Checking running processes..."

$process = Get-Process -Name "EasyPrinter" -ErrorAction SilentlyContinue
if ($process) {
    Write-Info "Closing EasyPrinter..."
    $process | Stop-Process -Force
    Start-Sleep -Seconds 2
    Write-Success "EasyPrinter closed"
}

# 2. Update from Git
Write-Info "Getting updates from Git..."

Push-Location $SourcePath

try {
    # Reset local changes
    & git reset --hard HEAD
    & git clean -fd

    # Pull updates
    $output = & git pull origin main 2>&1

    if ($LASTEXITCODE -ne 0) {
        throw "git pull error: $output"
    }

    if ($output -match "Already up to date") {
        Write-Success "Already up to date"
    } else {
        Write-Success "Updates downloaded"
    }
} catch {
    Write-Err "Update error: $_"
    Pop-Location
    Read-Host "Press Enter to exit"
    exit 1
}

# 3. Rebuild application
Write-Info "Rebuilding application..."

Push-Location (Join-Path $SourcePath "src\EasyPrinter")

try {
    # Restore dependencies
    & dotnet restore

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to restore packages"
    }

    # Build application
    & dotnet publish -c Release -o $InstallPath --self-contained false

    if ($LASTEXITCODE -ne 0) {
        throw "Build failed"
    }

    Write-Success "Application updated"
} catch {
    Write-Err "Build error: $_"
    Pop-Location
    Pop-Location
    Read-Host "Press Enter to exit"
    exit 1
}

Pop-Location
Pop-Location

# Completion
Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "      Update complete!" -ForegroundColor White
Write-Host "================================================" -ForegroundColor Green
Write-Host ""

# Ask to launch
$exePath = Join-Path $InstallPath "EasyPrinter.exe"
$response = Read-Host "Launch EasyPrinter now? (Y/N)"
if ($response -eq "Y" -or $response -eq "y") {
    Start-Process $exePath
}

Read-Host "Press Enter to exit"
