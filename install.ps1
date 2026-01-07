#Requires -RunAsAdministrator
<#
.SYNOPSIS
    Установочный скрипт для EasyPrinter
.DESCRIPTION
    Скрипт устанавливает все необходимые зависимости и собирает приложение EasyPrinter
    для управления HP LaserJet M1536dnf MFP
.NOTES
    Требуется запуск от имени администратора
#>

param(
    [string]$InstallPath = "C:\Program Files\EasyPrinter",
    [string]$SourcePath = "C:\ProgramData\EasyPrinter-src",
    [string]$RepoUrl = "https://github.com/arty-spr/easyprinter.git"
)

# Цвета для вывода
function Write-ColorOutput($ForegroundColor) {
    $fc = $host.UI.RawUI.ForegroundColor
    $host.UI.RawUI.ForegroundColor = $ForegroundColor
    if ($args) {
        Write-Output $args
    }
    $host.UI.RawUI.ForegroundColor = $fc
}

function Write-Success($message) {
    Write-Host "[OK] " -ForegroundColor Green -NoNewline
    Write-Host $message
}

function Write-Info($message) {
    Write-Host "[INFO] " -ForegroundColor Cyan -NoNewline
    Write-Host $message
}

function Write-Warning($message) {
    Write-Host "[!] " -ForegroundColor Yellow -NoNewline
    Write-Host $message
}

function Write-Error($message) {
    Write-Host "[X] " -ForegroundColor Red -NoNewline
    Write-Host $message
}

# Баннер
Clear-Host
Write-Host "================================================" -ForegroundColor Blue
Write-Host "      EasyPrinter - Установка" -ForegroundColor White
Write-Host "      HP LaserJet M1536dnf MFP" -ForegroundColor Gray
Write-Host "================================================" -ForegroundColor Blue
Write-Host ""

# 1. Проверка версии Windows
Write-Info "Проверка системы..."
$os = Get-CimInstance Win32_OperatingSystem
$arch = (Get-CimInstance Win32_Processor).AddressWidth

if ($arch -ne 64) {
    Write-Error "Требуется 64-битная версия Windows"
    exit 1
}

$winVersion = [System.Environment]::OSVersion.Version
if ($winVersion.Major -lt 10) {
    Write-Error "Требуется Windows 10 или новее"
    exit 1
}

Write-Success "Windows $($os.Caption) x64"

# 2. Проверка/установка .NET 6 Runtime
Write-Info "Проверка .NET 6 Desktop Runtime..."
$dotnetInstalled = $false

try {
    $runtimes = & dotnet --list-runtimes 2>$null
    if ($runtimes -match "Microsoft.WindowsDesktop.App 6\.") {
        $dotnetInstalled = $true
        Write-Success ".NET 6 Desktop Runtime уже установлен"
    }
} catch {
    # dotnet не найден
}

if (-not $dotnetInstalled) {
    Write-Info "Установка .NET 6 Desktop Runtime..."

    $dotnetUrl = "https://download.visualstudio.microsoft.com/download/pr/513d13b7-b456-45af-828b-b7b7981ff462/edf44a743b78f8b54a2cec97ce888346/windowsdesktop-runtime-6.0.33-win-x64.exe"
    $dotnetInstaller = "$env:TEMP\dotnet6-runtime.exe"

    try {
        Write-Info "Загрузка .NET 6 Runtime..."
        Invoke-WebRequest -Uri $dotnetUrl -OutFile $dotnetInstaller -UseBasicParsing

        Write-Info "Запуск установщика..."
        Start-Process -FilePath $dotnetInstaller -ArgumentList "/install /quiet /norestart" -Wait

        Remove-Item $dotnetInstaller -Force
        Write-Success ".NET 6 Desktop Runtime установлен"
    } catch {
        Write-Error "Не удалось установить .NET 6 Runtime: $_"
        Write-Warning "Пожалуйста, установите вручную: https://dotnet.microsoft.com/download/dotnet/6.0"
        exit 1
    }
}

# 3. Проверка Git
Write-Info "Проверка Git..."
$gitInstalled = $false

try {
    $gitVersion = & git --version 2>$null
    if ($gitVersion) {
        $gitInstalled = $true
        Write-Success "Git установлен: $gitVersion"
    }
} catch {
    # Git не найден
}

if (-not $gitInstalled) {
    Write-Error "Git не установлен!"
    Write-Warning "Пожалуйста, установите Git: https://git-scm.com/download/win"
    exit 1
}

# 4. Клонирование репозитория
Write-Info "Подготовка исходного кода..."

if (Test-Path $SourcePath) {
    Write-Info "Папка уже существует, обновляем..."
    Push-Location $SourcePath
    & git pull origin main
    Pop-Location
} else {
    Write-Info "Клонирование репозитория..."
    & git clone $RepoUrl $SourcePath

    if ($LASTEXITCODE -ne 0) {
        Write-Error "Не удалось клонировать репозиторий"
        exit 1
    }
}

Write-Success "Исходный код готов"

# 5. Сборка приложения
Write-Info "Сборка приложения..."

$projectPath = Join-Path $SourcePath "src\EasyPrinter\EasyPrinter.csproj"

if (-not (Test-Path $projectPath)) {
    Write-Error "Файл проекта не найден: $projectPath"
    exit 1
}

Push-Location (Join-Path $SourcePath "src\EasyPrinter")

try {
    # Восстанавливаем зависимости
    Write-Info "Восстановление NuGet пакетов..."
    & dotnet restore

    if ($LASTEXITCODE -ne 0) {
        throw "Ошибка восстановления пакетов"
    }

    # Собираем приложение
    Write-Info "Компиляция..."
    & dotnet publish -c Release -o $InstallPath --self-contained false

    if ($LASTEXITCODE -ne 0) {
        throw "Ошибка сборки"
    }

    Write-Success "Приложение собрано"
} catch {
    Write-Error "Ошибка сборки: $_"
    Pop-Location
    exit 1
}

Pop-Location

# 6. Создание ярлыка на рабочем столе
Write-Info "Создание ярлыка на рабочем столе..."

$desktopPath = [Environment]::GetFolderPath("CommonDesktopDirectory")
$shortcutPath = Join-Path $desktopPath "EasyPrinter.lnk"
$exePath = Join-Path $InstallPath "EasyPrinter.exe"

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath = $exePath
$shortcut.WorkingDirectory = $InstallPath
$shortcut.Description = "Управление HP LaserJet M1536dnf MFP"
$shortcut.Save()

Write-Success "Ярлык создан на рабочем столе"

# 7. Создание ярлыка для обновления
Write-Info "Создание ярлыка для обновления..."

$updateShortcutPath = Join-Path $InstallPath "Обновить EasyPrinter.lnk"
$updateScript = Join-Path $SourcePath "update.ps1"

$shortcut2 = $shell.CreateShortcut($updateShortcutPath)
$shortcut2.TargetPath = "powershell.exe"
$shortcut2.Arguments = "-ExecutionPolicy Bypass -File `"$updateScript`""
$shortcut2.WorkingDirectory = $SourcePath
$shortcut2.Description = "Обновить EasyPrinter"
$shortcut2.Save()

Write-Success "Ярлык для обновления создан"

# Завершение
Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "      Установка завершена!" -ForegroundColor White
Write-Host "================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Приложение установлено в: $InstallPath" -ForegroundColor Cyan
Write-Host "Исходный код: $SourcePath" -ForegroundColor Cyan
Write-Host ""
Write-Host "Для запуска используйте ярлык на рабочем столе" -ForegroundColor Yellow
Write-Host "Для обновления запустите: $updateScript" -ForegroundColor Yellow
Write-Host ""

# Запрос на запуск приложения
$response = Read-Host "Запустить EasyPrinter сейчас? (Y/N)"
if ($response -eq "Y" -or $response -eq "y") {
    Start-Process $exePath
}
