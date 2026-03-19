# status.ps1
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "📊 СТАТУС ПРОЕКТА" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Основные файлы
Write-Host "1. Основные файлы:" -ForegroundColor Yellow
$coreFiles = @(
    "run_fixed.py", "app.py", "predictor.py", "telegram_bot.py",
    "stats_reporter.py", "translations.py", "api_client.py",
    "models.py", "config.py", "team_form.py", "betting_optimizer.py"
)

$allOk = $true
foreach ($file in $coreFiles) {
    if (Test-Path $file) {
        $size = (Get-Item $file).Length
        $sizeKB = [math]::Round($size/1KB, 2)
        Write-Host "  ✅ $file ($sizeKB KB)" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file" -ForegroundColor Red
        $allOk = $false
    }
}

# Папка data
Write-Host ""
Write-Host "2. Папка data:" -ForegroundColor Yellow
if (Test-Path "data") {
    $totalFiles = (Get-ChildItem -Path "data" -Recurse -File).Count
    Write-Host "  📁 data/ - $totalFiles файлов" -ForegroundColor Green
    
    Get-ChildItem -Path "data" -Directory | ForEach-Object {
        $count = (Get-ChildItem -Path $_.FullName -File).Count
        Write-Host "    📁 $($_.Name)/ - $count файлов" -ForegroundColor Gray
    }
} else {
    Write-Host "  ❌ Папка data не найдена" -ForegroundColor Red
}

# Python cache
Write-Host ""
Write-Host "3. Временные файлы:" -ForegroundColor Yellow
$pycache = Get-ChildItem -Path . -Filter "__pycache__" -Recurse -Directory
if ($pycache) {
    Write-Host "  ⚠️ Найдены папки __pycache__:" -ForegroundColor Yellow
    foreach ($dir in $pycache) {
        Write-Host "    - $($dir.FullName)" -ForegroundColor Yellow
    }
} else {
    Write-Host "  ✅ Чисто" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Read-Host "Нажмите Enter для выхода"