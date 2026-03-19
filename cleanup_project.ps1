# cleanup_project.ps1
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🧹 ОЧИСТКА ПРОЕКТА" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Список файлов для удаления (временные, тестовые, бэкапы)
$files_to_delete = @(
    # Временные файлы Python
    "*.pyc",
    "*.pyo",
    "*.pyd",
    "__pycache__",
    
    # Логи и данные
    "*.log",
    "*.log.*",
    "*.backup",
    "*.back",
    "*.tmp",
    "*.temp",
    
    # Тестовые файлы (которые не используются)
    "test_*.py",
    "debug_*.py",
    "diagnose_*.py",
    "!test_telegram.py",  # Сохраняем этот
    
    # Xray файлы (если не используются)
    "xray/",
    "xray.exe",
    
    # Всякие временные файлы Windows
    "Thumbs.db",
    "desktop.ini",
    "*.DS_Store"
)

Write-Host "🔍 Поиск файлов для удаления..." -ForegroundColor Yellow
Write-Host ""

$total_size = 0
$total_files = 0

foreach ($pattern in $files_to_delete) {
    # Проверяем, начинается ли с ! (исключение)
    if ($pattern.StartsWith('!')) {
        $actual_pattern = $pattern.Substring(1)
        Write-Host "  ⚠️ Сохраняем: $actual_pattern" -ForegroundColor Green
        continue
    }
    
    # Ищем файлы по паттерну
    $files = Get-ChildItem -Path . -Recurse -Filter $pattern -ErrorAction SilentlyContinue
    
    foreach ($file in $files) {
        if ($file.PSIsContainer) {
            # Это папка
            $size = (Get-ChildItem $file.FullName -Recurse | Measure-Object Length -Sum).Sum
            $size_mb = [math]::Round($size/1MB, 2)
            Write-Host "  📁 $($file.FullName) - $size_mb MB" -ForegroundColor Red
            $total_size += $size
            $total_files += (Get-ChildItem $file.FullName -Recurse | Measure-Object).Count
        } else {
            # Это файл
            $size_kb = [math]::Round($file.Length/1KB, 2)
            Write-Host "  📄 $($file.FullName) - $size_kb KB" -ForegroundColor Red
            $total_size += $file.Length
            $total_files++
        }
    }
}

$total_size_mb = [math]::Round($total_size/1MB, 2)

Write-Host ""
Write-Host "📊 Найдено файлов для удаления: $total_files" -ForegroundColor Yellow
Write-Host "📊 Общий размер: $total_size_mb MB" -ForegroundColor Yellow
Write-Host ""

if ($total_files -eq 0) {
    Write-Host "✅ Нет файлов для удаления. Проект чист!" -ForegroundColor Green
} else {
    Write-Host "❓ Удалить эти файлы? (Y/N)" -ForegroundColor Yellow
    $answer = Read-Host
    
    if ($answer -eq 'Y' -or $answer -eq 'y') {
        Write-Host ""
        Write-Host "🗑 Удаление..." -ForegroundColor Yellow
        
        foreach ($pattern in $files_to_delete) {
            if ($pattern.StartsWith('!')) {
                continue
            }
            
            # Удаляем файлы и папки
            Get-ChildItem -Path . -Recurse -Filter $pattern -ErrorAction SilentlyContinue | ForEach-Object {
                if ($_.PSIsContainer) {
                    Remove-Item -Path $_.FullName -Recurse -Force -ErrorAction SilentlyContinue
                    Write-Host "  ✅ Удалена папка: $($_.FullName)" -ForegroundColor Green
                } else {
                    Remove-Item -Path $_.FullName -Force -ErrorAction SilentlyContinue
                    Write-Host "  ✅ Удален файл: $($_.FullName)" -ForegroundColor Green
                }
            }
        }
        
        Write-Host ""
        Write-Host "✅ Очистка завершена!" -ForegroundColor Green
    } else {
        Write-Host ""
        Write-Host "⏹ Очистка отменена" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
pause