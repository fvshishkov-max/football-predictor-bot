@echo off
chcp 65001 >nul
echo ========================================
echo 📜 ПРОСМОТР ЛОГОВ
echo ========================================
echo.
if exist data\logs\app.log (
    type data\logs\app.log
) else (
    echo Лог-файл не найден
)
echo.
echo ========================================
pause