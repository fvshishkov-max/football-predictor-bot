# collect_logs.ps1
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$folder = "analysis_$timestamp"
$zipFile = "analysis_$timestamp.zip"

Write-Host "Сбор файлов для анализа..." -ForegroundColor Green
Write-Host ""

# Создаем папку
New-Item -ItemType Directory -Path $folder -Force | Out-Null

# Копируем файлы
$files = @(
    "signal_accuracy.json",
    "bot_stats.json", 
    "football_bot.log"
)

foreach ($file in $files) {
    if (Test-Path $file) {
        Copy-Item $file -Destination $folder
        Write-Host "✅ $file" -ForegroundColor Green
    } else {
        Write-Host "❌ $file не найден" -ForegroundColor Red
    }
}

# Копируем последний signals_history файл
$signalFiles = Get-ChildItem -Path . -Filter "signals_history_*.json" | Sort-Object LastWriteTime -Descending
if ($signalFiles.Count -gt 0) {
    $latest = $signalFiles[0].Name
    Copy-Item $latest -Destination $folder
    Write-Host "✅ $latest" -ForegroundColor Green
} else {
    Write-Host "❌ signals_history_*.json не найдены" -ForegroundColor Red
}

# Создаем архив
if (Test-Path $folder) {
    Compress-Archive -Path "$folder\*" -DestinationPath $zipFile -Force
    Write-Host ""
    Write-Host "✅ Архив создан: $zipFile" -ForegroundColor Green
    Write-Host "📁 Размер: $((Get-Item $zipFile).Length / 1KB) KB"
    
    # Удаляем временную папку
    Remove-Item $folder -Recurse -Force
}

Write-Host ""
Write-Host "Отправьте файл $zipFile на анализ." -ForegroundColor Yellow