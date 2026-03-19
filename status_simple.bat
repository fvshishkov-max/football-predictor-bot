@echo off
chcp 1251 >nul
title Статус проекта
color 0A

echo ========================================
echo 📊 СТАТУС ПРОЕКТА
echo ========================================
echo.

echo 1. Основные файлы:
echo ------------------
set count=0

for %%f in (run_fixed.py app.py predictor.py telegram_bot.py stats_reporter.py translations.py) do (
    if exist %%f (
        echo   [OK] %%f
        set /a count+=1
    ) else (
        echo   [--] %%f
    )
)
echo   Всего: %count% файлов
echo.

echo 2. Папка data:
echo --------------
if exist data (
    dir data /s /b | find /c /v "" > temp.txt
    set /p files=<temp.txt
    del temp.txt
    echo   Найдено %files% файлов
    echo.
    dir data /ad /b
) else (
    echo   Папка data не найдена
)
echo.

echo 3. Временные файлы:
echo --------------------
dir /s /b *.pyc __pycache__ 2>nul | find /c /v "" > temp.txt
set /p pycache=<temp.txt
del temp.txt
if %pycache% gtr 0 (
    echo   ⚠️ Найдено %pycache% временных файлов
) else (
    echo   ✅ Чисто
)

echo.
echo ========================================
pause