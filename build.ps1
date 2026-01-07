<#
.SYNOPSIS
    Скрипт сборки EasyPrinter для разработки
.DESCRIPTION
    Собирает приложение в текущей директории
#>

param(
    [ValidateSet("Debug", "Release")]
    [string]$Configuration = "Release",

    [string]$OutputPath = ".\publish"
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
Write-Host ""
Write-Host "EasyPrinter - Сборка ($Configuration)" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

$projectPath = Join-Path $PSScriptRoot "src\EasyPrinter\EasyPrinter.csproj"

if (-not (Test-Path $projectPath)) {
    Write-Error "Файл проекта не найден: $projectPath"
    exit 1
}

Push-Location (Join-Path $PSScriptRoot "src\EasyPrinter")

try {
    # Восстанавливаем зависимости
    Write-Info "Восстановление NuGet пакетов..."
    & dotnet restore

    if ($LASTEXITCODE -ne 0) {
        throw "Ошибка восстановления пакетов"
    }
    Write-Success "Пакеты восстановлены"

    # Собираем приложение
    Write-Info "Компиляция ($Configuration)..."
    & dotnet build -c $Configuration

    if ($LASTEXITCODE -ne 0) {
        throw "Ошибка компиляции"
    }
    Write-Success "Компиляция успешна"

    # Публикуем
    Write-Info "Публикация в $OutputPath..."
    & dotnet publish -c $Configuration -o $OutputPath --self-contained false

    if ($LASTEXITCODE -ne 0) {
        throw "Ошибка публикации"
    }
    Write-Success "Опубликовано в: $OutputPath"

} catch {
    Write-Error "Ошибка: $_"
    Pop-Location
    exit 1
}

Pop-Location

Write-Host ""
Write-Host "Сборка завершена!" -ForegroundColor Green
Write-Host "Запустите: $OutputPath\EasyPrinter.exe" -ForegroundColor Yellow
Write-Host ""
