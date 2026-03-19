@echo off
echo ========================================
echo ARCHIVING OLD FILES
echo ========================================
echo.

REM Создаем папку для архивов
mkdir archives 2>nul
set timestamp=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%%time:~6,2%
set timestamp=%timestamp: =0%
set archive_name=archives\backup_%timestamp%.zip

echo Creating archive: %archive_name%

REM Устанавливаем путь к 7zip (если есть)
set sevenzip="C:\Program Files\7-Zip\7z.exe"

if exist %sevenzip% (
    %sevenzip% a -tzip %archive_name% signals_history_*.csv predictions_history_*.csv predictions_stats_*.txt *.log *.backup *.back 2>nul
    echo [OK] Archive created with 7zip
) else (
    echo 7zip not found, skipping archive creation
    echo You can manually archive old files
)

echo.
echo ========================================
pause