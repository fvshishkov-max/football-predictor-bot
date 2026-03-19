@echo off
chcp 65001 >nul
title Быстрый старт
color 0A

echo ========================================
echo 🚀 БЫСТРЫЙ СТАРТ
echo ========================================
echo.

echo 1. Настройка структуры проекта...
call setup_project.bat

echo.
echo 2. Очистка временных файлов...
call clean_temp.bat

echo.
echo 3. Обновление путей в файлах...
python update_config.py

echo.
echo 4. Запуск бота...
echo.
echo ========================================
python run_fixed.py

pause