# organize.ps1
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🔧 ОРГАНИЗАЦИЯ ПРОЕКТА" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Создание папок
Write-Host "1. Создание папок..." -ForegroundColor Yellow
$folders = @(
    "data\predictions",
    "data\history",
    "data\stats",
    "data\logs",
    "data\backups",
    "data\models",
    "data\cache",
    "archives"
)

foreach ($folder in $folders) {
    New-Item -ItemType Directory -Force -Path $folder | Out-Null
    Write-Host "  ✅ $folder" -ForegroundColor Green
}

# 2. Перемещение файлов
Write-Host ""
Write-Host "2. Перемещение файлов..." -ForegroundColor Yellow

# Файлы предсказаний
Get-ChildItem -Path . -Filter "predictions_history_*.csv" | Move-Item -Destination "data\history\" -ErrorAction SilentlyContinue
Get-ChildItem -Path . -Filter "signals_history_*.csv" | Move-Item -Destination "data\history\" -ErrorAction SilentlyContinue
Get-ChildItem -Path . -Filter "predictions_stats_*.txt" | Move-Item -Destination "data\stats\" -ErrorAction SilentlyContinue
Get-ChildItem -Path . -Filter "predictions_stats_*.json" | Move-Item -Destination "data\stats\" -ErrorAction SilentlyContinue

# Основные файлы
if (Test-Path "predictions.json") { Move-Item -Path "predictions.json" -Destination "data\predictions\" -Force }
if (Test-Path "prediction_stats.json") { Move-Item -Path "prediction_stats.json" -Destination "data\stats\" -Force }
if (Test-Path "xgboost_model.pkl") { Move-Item -Path "xgboost_model.pkl" -Destination "data\models\" -Force }
if (Test-Path "xgboost_model_features.json") { Move-Item -Path "xgboost_model_features.json" -Destination "data\models\" -Force }

# Базы данных
if (Test-Path "matches_history.db") { Move-Item -Path "matches_history.db" -Destination "data\history\" -Force }
if (Test-Path "football_cache.db") { Move-Item -Path "football_cache.db" -Destination "data\cache\" -Force }

# Логи
Get-ChildItem -Path . -Filter "*.log" | Move-Item -Destination "data\logs\" -ErrorAction SilentlyContinue

# Бэкапы
Get-ChildItem -Path . -Filter "*.backup" | Move-Item -Destination "data\backups\" -ErrorAction SilentlyContinue
Get-ChildItem -Path . -Filter "*.back" | Move-Item -Destination "data\backups\" -ErrorAction SilentlyContinue

Write-Host "  ✅ Файлы перемещены" -ForegroundColor Green

# 3. Очистка временных файлов
Write-Host ""
Write-Host "3. Очистка временных файлов..." -ForegroundColor Yellow

# Удаляем Python cache
Get-ChildItem -Path . -Filter "*.pyc" -Recurse | Remove-Item -Force -ErrorAction SilentlyContinue
Get-ChildItem -Path . -Filter "__pycache__" -Recurse -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue

Write-Host "  ✅ Временные файлы удалены" -ForegroundColor Green

# 4. Проверка результата
Write-Host ""
Write-Host "4. Результат:" -ForegroundColor Yellow
Write-Host ""

if (Test-Path "data") {
    $fileCount = (Get-ChildItem -Path "data" -Recurse -File).Count
    Write-Host "  📁 data/ - $fileCount файлов" -ForegroundColor Green
    
    # Показываем структуру
    Get-ChildItem -Path "data" -Directory | ForEach-Object {
        $subCount = (Get-ChildItem -Path $_.FullName -File).Count
        Write-Host "    📁 $($_.Name)/ - $subCount файлов" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ ОРГАНИЗАЦИЯ ЗАВЕРШЕНА" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan

Read-Host "`nНажмите Enter для выхода"