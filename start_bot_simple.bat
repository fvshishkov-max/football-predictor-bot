@echo off
chcp 1251 >nul
title Запуск бота
color 0A

echo ========================================
echo 🚀 ЗАПУСК БОТА
echo ========================================
echo.

if not exist run_fixed.py (
    echo ❌ Файл run_fixed.py не найден!
    pause
    exit /b
)

echo Запуск бота...
echo.
python run_fixed.py

pause