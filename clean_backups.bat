@echo off
chcp 65001 >nul
title Очистка резервных копий
color 0A

echo ========================================
echo 🧹 ОЧИСТКА РЕЗЕРВНЫХ КОПИЙ
echo ========================================
echo.

echo Найдены папки с резервными копиями:
dir /ad backup_* 2>nul
echo.

set /p "DELETE=Удалить все папки backup_*? (Y/N): "

if /i "%DELETE%"=="Y" (
    for /d %%d in (backup_*) do (
        echo Удаление: %%d
        rmdir /s /q %%d
    )
    echo ✅ Резервные копии удалены
) else (
    echo ⏹ Очистка отменена
)

echo.
pause