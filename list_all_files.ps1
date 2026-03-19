# list_all_files.ps1
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "📋 СПИСОК ВСЕХ ФАЙЛОВ" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$files = Get-ChildItem -File -Recurse | Sort-Object FullName

$current_dir = ""
foreach ($file in $files) {
    $dir = Split-Path $file.FullName -Parent
    if ($dir -ne $current_dir) {
        Write-Host ""
        Write-Host "📁 $dir" -ForegroundColor Yellow
        $current_dir = $dir
    }
    
    $size_kb = [math]::Round($file.Length/1KB, 2)
    $size_str = if ($size_kb -gt 1024) { 
        [math]::Round($size_kb/1024, 2).ToString() + " MB"
    } else { 
        $size_kb.ToString() + " KB"
    }
    
    Write-Host "  📄 $($file.Name) ($size_str)" -ForegroundColor White
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "📊 Всего файлов: $($files.Count)" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
pause