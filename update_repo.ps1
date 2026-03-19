# update_repo.ps1
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "📦 ОБНОВЛЕНИЕ РЕПОЗИТОРИЯ" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Проверяем статус
Write-Host "📊 Проверка статуса Git..." -ForegroundColor Yellow
git status

Write-Host ""
Write-Host "❓ Добавить все изменения? (Y/N)" -ForegroundColor Yellow
$answer = Read-Host

if ($answer -eq 'Y' -or $answer -eq 'y') {
    # Добавляем все файлы
    Write-Host ""
    Write-Host "📦 Добавление файлов..." -ForegroundColor Yellow
    git add .
    
    # Проверяем, что добавили
    Write-Host ""
    Write-Host "📊 Статус после добавления:" -ForegroundColor Yellow
    git status
    
    Write-Host ""
    Write-Host "📝 Введите комментарий к коммиту:" -ForegroundColor Yellow
    $commit_message = Read-Host
    
    if ($commit_message -eq '') {
        $commit_message = "Update: " + (Get-Date -Format "yyyy-MM-dd HH:mm")
    }
    
    # Создаем коммит
    Write-Host ""
    Write-Host "💾 Создание коммита..." -ForegroundColor Yellow
    git commit -m $commit_message
    
    # Пушим изменения
    Write-Host ""
    Write-Host "☁️ Отправка на GitHub..." -ForegroundColor Yellow
    git push origin main
    
    Write-Host ""
    Write-Host "✅ Репозиторий обновлен!" -ForegroundColor Green
} else {
    Write-Host ""
    Write-Host "⏹ Обновление отменено" -ForegroundColor Red
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
pause