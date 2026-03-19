@echo off
chcp 65001 >nul
title Проверка проекта
color 0A

echo ========================================
echo 🔍 ПРОВЕРКА ПРОЕКТА
echo ========================================
echo.

echo 📋 Основные файлы:
echo -----------------
set missing=0

call :check_file run_fixed.py
call :check_file app.py
call :check_file predictor.py
call :check_file telegram_bot.py
call :check_file stats_reporter.py
call :check_file translations.py
call :check_file api_client.py
call :check_file models.py
call :check_file config.py
call :check_file team_form.py
call :check_file betting_optimizer.py

echo.
if %missing% equ 0 (
    echo ✅ Все основные файлы на месте
) else (
    echo ⚠️ Отсутствует %missing% файлов
)

echo.
echo 📊 Статистика:
echo -----------------
set pycount=0
for %%f in (*.py) do set /a pycount+=1
echo   • Python файлов: %pycount%

if exist data (
    set datacount=0
    for %%f in (data\*) do set /a datacount+=1
    echo   • Файлов в data: %datacount%
) else (
    echo   • Папка data: не найдена
)

if exist xray (
    echo   • Папка xray: найдена
) else (
    echo   • Папка xray: не найдена
)

echo.
echo ========================================
pause
exit /b

:check_file
if exist %1 (
    echo   ✅ %1
) else (
    echo   ❌ %1
    set /a missing+=1
)
exit /b