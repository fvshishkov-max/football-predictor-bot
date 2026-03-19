@echo off
chcp 1251 >nul
title Диагностика статистики
color 0A

echo ========================================
echo 🔍 ДИАГНОСТИКА СТАТИСТИКИ
echo ========================================
echo.

echo 1. Проверка файла с предсказаниями...
python tools/check_predictions_file.py
echo.

echo 2. Просмотр последних предсказаний...
python tools/show_predictions.py
echo.

echo 3. Исправление формата дат...
python tools/fix_predictions_format.py
echo.

echo 4. Проверка общей статистики...
python tools/run_stats.py
echo.

echo ========================================
pause
