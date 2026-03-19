# clean_all.ps1
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🧹 ПОЛНАЯ ОЧИСТКА" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "⚠️  ВНИМАНИЕ! Будут удалены:" -ForegroundColor Red
Write-Host "   - Все временные файлы Python"
Write-Host "   - Все файлы логов"
Write-Host "   - Все файлы бэкапов"
Write-Host "   - Папка __pycache__"
Write-Host ""

$confirm = Read-Host "Продолжить? (Y/N)"

if ($confirm -eq "Y" -or $confirm -eq "y") {
    Write-Host ""
    Write-Host "1. Удаление Python cache..." -ForegroundColor Yellow
    Get-ChildItem -Path . -Filter "*.pyc" -Recurse | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path . -Filter "__pycache__" -Recurse -Directory | Remove-Item -Recurse -Force -ErrorAction SilentlyContinue
    Write-Host "   ✅ Готово" -ForegroundColor Green
    
    Write-Host "2. Удаление логов..." -ForegroundColor Yellow
    Get-ChildItem -Path . -Filter "*.log" -Recurse | Remove-Item -Force -ErrorAction SilentlyContinue
    Write-Host "   ✅ Готово" -ForegroundColor Green
    
    Write-Host "3. Удаление бэкапов..." -ForegroundColor Yellow
    Get-ChildItem -Path . -Filter "*.backup" -Recurse | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path . -Filter "*.back" -Recurse | Remove-Item -Force -ErrorAction SilentlyContinue
    Write-Host "   ✅ Готово" -ForegroundColor Green
    
    Write-Host "4. Удаление временных файлов..." -ForegroundColor Yellow
    Get-ChildItem -Path . -Filter "*.tmp" -Recurse | Remove-Item -Force -ErrorAction SilentlyContinue
    Get-ChildItem -Path . -Filter "*.temp" -Recurse | Remove-Item -Force -ErrorAction SilentlyContinue
    Write-Host "   ✅ Готово" -ForegroundColor Green
    
    Write-Host ""
    Write-Host "✅ Очистка завершена!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "⏹ Очистка отменена" -ForegroundColor Yellow
}

Read-Host "`nНажмите Enter для выхода"