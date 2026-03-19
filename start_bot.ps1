# start_bot.ps1
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🚀 ЗАПУСК БОТА" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Проверяем наличие необходимых файлов
$required = @("run_fixed.py", "app.py", "predictor.py")
$missing = @()

foreach ($file in $required) {
    if (-not (Test-Path $file)) {
        $missing += $file
    }
}

if ($missing.Count -gt 0) {
    Write-Host "❌ Отсутствуют файлы:" -ForegroundColor Red
    foreach ($file in $missing) {
        Write-Host "   - $file" -ForegroundColor Red
    }
} else {
    Write-Host "✅ Все файлы на месте" -ForegroundColor Green
    Write-Host ""
    Write-Host "Запуск бота..." -ForegroundColor Yellow
    Write-Host ""
    
    python run_fixed.py
}

Read-Host "`nНажмите Enter для выхода"