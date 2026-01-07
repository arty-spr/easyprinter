<#
.SYNOPSIS
    Скрипт обновления EasyPrinter
.DESCRIPTION
    Скачивает последнюю версию из Git и пересобирает приложение
#>

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

function Write-Error($message) {
    Write-Host "[X] " -ForegroundColor Red -NoNewline
    Write-Host $message
}

# Баннер
Clear-Host
Write-Host "================================================" -ForegroundColor Blue
Write-Host "      EasyPrinter - Обновление" -ForegroundColor White
Write-Host "================================================" -ForegroundColor Blue
Write-Host ""

# Проверка наличия исходного кода
if (-not (Test-Path $SourcePath)) {
    Write-Error "Исходный код не найден: $SourcePath"
    Write-Host "Пожалуйста, сначала запустите install.ps1"
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

# 1. Закрытие EasyPrinter если запущен
Write-Info "Проверка запущенных процессов..."

$process = Get-Process -Name "EasyPrinter" -ErrorAction SilentlyContinue
if ($process) {
    Write-Info "Закрытие EasyPrinter..."
    $process | Stop-Process -Force
    Start-Sleep -Seconds 2
    Write-Success "EasyPrinter закрыт"
}

# 2. Обновление из Git
Write-Info "Получение обновлений из Git..."

Push-Location $SourcePath

try {
    # Сбрасываем локальные изменения
    & git reset --hard HEAD
    & git clean -fd

    # Получаем обновления
    $output = & git pull origin main 2>&1

    if ($LASTEXITCODE -ne 0) {
        throw "Ошибка git pull: $output"
    }

    if ($output -match "Already up to date") {
        Write-Success "Уже установлена последняя версия"
    } else {
        Write-Success "Обновления загружены"
    }
} catch {
    Write-Error "Ошибка обновления: $_"
    Pop-Location
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

# 3. Пересборка приложения
Write-Info "Пересборка приложения..."

Push-Location (Join-Path $SourcePath "src\EasyPrinter")

try {
    # Восстанавливаем зависимости
    & dotnet restore

    if ($LASTEXITCODE -ne 0) {
        throw "Ошибка восстановления пакетов"
    }

    # Собираем приложение
    & dotnet publish -c Release -o $InstallPath --self-contained false

    if ($LASTEXITCODE -ne 0) {
        throw "Ошибка сборки"
    }

    Write-Success "Приложение обновлено"
} catch {
    Write-Error "Ошибка сборки: $_"
    Pop-Location
    Pop-Location
    Read-Host "Нажмите Enter для выхода"
    exit 1
}

Pop-Location
Pop-Location

# Завершение
Write-Host ""
Write-Host "================================================" -ForegroundColor Green
Write-Host "      Обновление завершено!" -ForegroundColor White
Write-Host "================================================" -ForegroundColor Green
Write-Host ""

# Запрос на запуск приложения
$exePath = Join-Path $InstallPath "EasyPrinter.exe"
$response = Read-Host "Запустить EasyPrinter сейчас? (Y/N)"
if ($response -eq "Y" -or $response -eq "y") {
    Start-Process $exePath
}
