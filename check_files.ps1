# check_files.ps1
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "🔍 ПРОВЕРКА ФАЙЛОВ ПРОЕКТА" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Основные файлы
$core_files = @(
    "run_fixed.py",
    "app.py",
    "predictor.py",
    "telegram_bot.py",
    "stats_reporter.py",
    "translations.py",
    "api_client.py",
    "models.py",
    "config.py",
    "team_form.py",
    "betting_optimizer.py",
    "feature_engineering.py",
    "statistical_models.py",
    "advanced_features.py"
)

Write-Host "📋 Основные файлы:" -ForegroundColor Yellow
foreach ($file in $core_files) {
    if (Test-Path $file) {
        $size = (Get-Item $file).Length
        $size_kb = [math]::Round($size/1024, 2)
        Write-Host "  ✅ $file ($size_kb KB)" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $file (не найден)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "📁 Папки:" -ForegroundColor Yellow

# Проверяем папку data
if (Test-Path "data") {
    $data_files = Get-ChildItem -Path "data" -File
    Write-Host "  📁 data/ - $($data_files.Count) файлов" -ForegroundColor Green
} else {
    Write-Host "  ❌ data/ - не найдена" -ForegroundColor Red
}

# Проверяем папку xray
if (Test-Path "xray") {
    $xray_files = Get-ChildItem -Path "xray" -File
    Write-Host "  📁 xray/ - $($xray_files.Count) файлов" -ForegroundColor Yellow
} else {
    Write-Host "  📁 xray/ - не найдена" -ForegroundColor Gray
}

Write-Host ""
Write-Host "📊 Статистика:" -ForegroundColor Yellow

# Общее количество файлов
$all_files = Get-ChildItem -File -Recurse
$total_size = ($all_files | Measure-Object -Property Length -Sum).Sum
$total_size_mb = [math]::Round($total_size/1MB, 2)

Write-Host "  • Всего файлов: $($all_files.Count)"
Write-Host "  • Общий размер: $total_size_mb MB"

# Файлы по расширениям
$extensions = $all_files | Group-Object Extension | Sort-Object Count -Descending
Write-Host ""
Write-Host "📄 Расширения файлов:" -ForegroundColor Yellow
foreach ($ext in $extensions) {
    $ext_name = if ($ext.Name -eq '') { '(без расширения)' } else { $ext.Name }
    Write-Host "  • $ext_name : $($ext.Count) файлов"
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
pause