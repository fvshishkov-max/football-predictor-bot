@echo off
chcp 65001 >nul
title Планировщик обновлений
color 0A

echo ========================================
echo 🔄 ЗАПУСК ПЛАНИРОВЩИКА ОБНОВЛЕНИЙ
echo ========================================
echo.

echo Установка зависимостей...
pip install schedule 2>nul

echo.
echo Запуск планировщика...
echo Для остановки закройте это окно
echo.

python simple_updater.py

pause